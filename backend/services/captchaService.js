const verifyCaptchaToken = async (captchaToken, remoteIp) => {
  const secret = process.env.TURNSTILE_SECRET_KEY;

  if (!secret) {
    if (process.env.NODE_ENV !== 'production' && captchaToken === 'dev-bypass') {
      return true;
    }
    return false;
  }

  if (!captchaToken) {
    return false;
  }

  const formData = new URLSearchParams();
  formData.append('secret', secret);
  formData.append('response', captchaToken);
  if (remoteIp) {
    formData.append('remoteip', remoteIp);
  }

  const response = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: formData.toString()
  });

  const payload = await response.json();
  return Boolean(payload.success);
};

module.exports = {
  verifyCaptchaToken
};
