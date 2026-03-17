#!/usr/bin/env python3

import json
import logging
import os
import smtplib
import ssl
import time
from datetime import datetime, timezone
from email.message import EmailMessage

import docker


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


PROJECT_NAME = os.environ.get('SERVICE_MONITOR_PROJECT_NAME', 'emailfilter')
MONITORED_SERVICES = [
    service.strip()
    for service in os.environ.get(
        'SERVICE_MONITOR_SERVICES',
        'detectish,backend,frontend,clamav,mysql,email-ingestion',
    ).split(',')
    if service.strip()
]
ALERT_RECIPIENTS = [
    recipient.strip()
    for recipient in os.environ.get('SERVICE_ALERT_EMAIL', '').split(',')
    if recipient.strip()
]
POLL_INTERVAL_SECONDS = int(os.environ.get('SERVICE_ALERT_POLL_INTERVAL_SECONDS', '60'))
FAILURE_THRESHOLD = int(os.environ.get('SERVICE_ALERT_FAILURE_THRESHOLD', '2'))
STATE_FILE = os.environ.get('SERVICE_ALERT_STATE_FILE', '/data/state.json')

SMTP_HOST = os.environ['SMTP_HOST']
SMTP_PORT = int(os.environ.get('SMTP_PORT', '465'))
SMTP_USER = os.environ['SMTP_USER']
SMTP_PASS = os.environ['SMTP_PASS']
SMTP_FROM = os.environ.get('SMTP_FROM', SMTP_USER)
SMTP_SECURE = os.environ.get('SMTP_SECURE', 'true').lower() == 'true'


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as state_file:
            return json.load(state_file)
    except Exception as exc:
        logger.warning('Failed to load monitor state: %s', exc)
        return {}


def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as state_file:
        json.dump(state, state_file, indent=2, sort_keys=True)


def get_service_snapshots(client: docker.DockerClient) -> dict:
    containers = client.containers.list(
        all=True,
        filters={'label': f'com.docker.compose.project={PROJECT_NAME}'},
    )
    service_to_container = {}
    for container in containers:
        service_name = container.labels.get('com.docker.compose.service')
        if service_name:
            service_to_container[service_name] = container

    snapshots = {}
    for service in MONITORED_SERVICES:
        container = service_to_container.get(service)
        if container is None:
            snapshots[service] = {
                'healthy': False,
                'summary': 'Container not found',
                'details': 'Compose service container is missing.',
            }
            continue

        container.reload()
        attrs = container.attrs
        state = attrs.get('State', {})
        runtime_status = state.get('Status', 'unknown')
        health = (state.get('Health') or {}).get('Status')

        healthy = runtime_status == 'running' and (health in (None, 'healthy'))
        summary = f'status={runtime_status}'
        if health:
            summary = f'{summary}, health={health}'

        details_parts = [
            f'Container: {container.name}',
            f'Runtime status: {runtime_status}',
        ]
        if health:
            details_parts.append(f'Health status: {health}')

        health_log = (state.get('Health') or {}).get('Log') or []
        if health_log:
            last_log = health_log[-1]
            output = (last_log.get('Output') or '').strip()
            if output:
                details_parts.append(f'Health output: {output}')

        snapshots[service] = {
            'healthy': healthy,
            'summary': summary,
            'details': ' | '.join(details_parts),
        }

    return snapshots


def send_email(subject: str, body: str):
    if not ALERT_RECIPIENTS:
        logger.warning('No alert recipients configured; skipping email: %s', subject)
        return

    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = SMTP_FROM
    message['To'] = ', '.join(ALERT_RECIPIENTS)
    message.set_content(body)

    context = ssl.create_default_context()
    if SMTP_SECURE and SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as smtp:
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(message)
        return

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        if SMTP_SECURE:
            smtp.starttls(context=context)
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(message)


def send_degraded_alert(service: str, snapshot: dict):
    subject = f'[Bakaya] Service degraded: {service}'
    body = (
        f'Service degradation detected at {utc_now()}.\n\n'
        f'Project: {PROJECT_NAME}\n'
        f'Service: {service}\n'
        f'Status: {snapshot["summary"]}\n'
        f'Details: {snapshot["details"]}\n'
    )
    send_email(subject, body)
    logger.warning('Sent degradation alert for %s', service)


def send_recovery_alert(service: str, snapshot: dict):
    subject = f'[Bakaya] Service recovered: {service}'
    body = (
        f'Service recovery detected at {utc_now()}.\n\n'
        f'Project: {PROJECT_NAME}\n'
        f'Service: {service}\n'
        f'Status: {snapshot["summary"]}\n'
        f'Details: {snapshot["details"]}\n'
    )
    send_email(subject, body)
    logger.info('Sent recovery alert for %s', service)


def reconcile_service_state(state: dict, service: str, snapshot: dict):
    service_state = state.setdefault(service, {'failures': 0, 'alerted': False})

    if snapshot['healthy']:
        if service_state.get('alerted'):
            send_recovery_alert(service, snapshot)
        service_state['failures'] = 0
        service_state['alerted'] = False
        service_state['last_summary'] = snapshot['summary']
        return

    service_state['failures'] = int(service_state.get('failures', 0)) + 1
    service_state['last_summary'] = snapshot['summary']
    if service_state['failures'] >= FAILURE_THRESHOLD and not service_state.get('alerted'):
        send_degraded_alert(service, snapshot)
        service_state['alerted'] = True


def main():
    logger.info(
        'Starting service monitor for project=%s services=%s poll_interval=%ss threshold=%s',
        PROJECT_NAME,
        ','.join(MONITORED_SERVICES),
        POLL_INTERVAL_SECONDS,
        FAILURE_THRESHOLD,
    )
    state = load_state()
    client = docker.from_env()

    while True:
        try:
            snapshots = get_service_snapshots(client)
            for service, snapshot in snapshots.items():
                reconcile_service_state(state, service, snapshot)
            save_state(state)
        except Exception as exc:
            logger.exception('Service monitor poll failed: %s', exc)

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == '__main__':
    main()