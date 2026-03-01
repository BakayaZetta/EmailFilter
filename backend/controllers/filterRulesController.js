const db = require('../config/db');

const ADMIN_ROLES = new Set(['admin', 'super_admin', 'superadmin']);
const isAdminUser = (req) => ADMIN_ROLES.has((req.userData?.role || '').toLowerCase());

let blacklistUserColumnChecked = false;
const ensureBlacklistUserColumn = async () => {
  if (blacklistUserColumnChecked) {
    return;
  }

  const [columns] = await db.query("SHOW COLUMNS FROM Blacklist LIKE 'ID_Utilisateur'");
  if (columns.length === 0) {
    await db.query('ALTER TABLE Blacklist ADD COLUMN ID_Utilisateur INT NULL');
    await db.query('CREATE INDEX idx_blacklist_user ON Blacklist (ID_Utilisateur)');
  }

  blacklistUserColumnChecked = true;
};

// Get all filter rules
exports.getFilterRules = async (req, res) => {
  try {
    await ensureBlacklistUserColumn();

    const [rules] = isAdminUser(req)
      ? await db.query('SELECT * FROM Blacklist ORDER BY created_at DESC')
      : await db.query(
          'SELECT * FROM Blacklist WHERE ID_Utilisateur = ? ORDER BY created_at DESC',
          [req.userData.userId]
        );
    
    res.json(rules);
  } catch (error) {
    console.error('Error fetching filter rules:', error);
    res.status(500).json({ message: 'Server error while fetching filter rules' });
  }
};

// Get specific filter rule
exports.getFilterRuleById = async (req, res) => {
  try {
    await ensureBlacklistUserColumn();

    const [rules] = await db.query('SELECT * FROM Blacklist WHERE ID_Blacklist = ?', [req.params.id]);
    
    if (rules.length === 0) {
      return res.status(404).json({ message: 'Filter rule not found' });
    }

    if (!isAdminUser(req) && String(rules[0].ID_Utilisateur) !== String(req.userData.userId)) {
      return res.status(403).json({ message: 'Forbidden' });
    }
    
    res.json(rules[0]);
  } catch (error) {
    console.error('Error fetching filter rule:', error);
    res.status(500).json({ message: 'Server error while fetching filter rule' });
  }
};

// Create a new filter rule
exports.createFilterRule = async (req, res) => {
  try {
    await ensureBlacklistUserColumn();

    const { sender_email } = req.body;
    
    // Validate input
    if (!sender_email) {
      return res.status(400).json({ message: 'Email address is required' });
    }
    
    // Check for duplicate
    const [existingRules] = isAdminUser(req)
      ? await db.query('SELECT * FROM Blacklist WHERE Email = ? AND ID_Utilisateur IS NULL', [sender_email])
      : await db.query(
          'SELECT * FROM Blacklist WHERE Email = ? AND ID_Utilisateur = ?',
          [sender_email, req.userData.userId]
        );
    
    if (existingRules.length > 0) {
      return res.status(400).json({ message: 'This email is already in the blocklist' });
    }
    
    // Insert rule
    const [result] = isAdminUser(req)
      ? await db.query(
          'INSERT INTO Blacklist (Email, ID_Utilisateur) VALUES (?, NULL)',
          [sender_email]
        )
      : await db.query(
          'INSERT INTO Blacklist (Email, ID_Utilisateur) VALUES (?, ?)',
          [sender_email, req.userData.userId]
        );
    
    // Return the new rule with its ID
    const [insertedRule] = await db.query(
      'SELECT * FROM Blacklist WHERE ID_Blacklist = ?',
      [result.insertId]
    );
    
    res.status(201).json(insertedRule[0]);
  } catch (error) {
    console.error('Error creating filter rule:', error);
    res.status(500).json({ message: 'Server error while creating filter rule' });
  }
};

// Update a filter rule
exports.updateFilterRule = async (req, res) => {
  try {
    await ensureBlacklistUserColumn();

    const { id } = req.params;
    const { sender_email } = req.body;
    
    // Validation
    if (!sender_email) {
      return res.status(400).json({ message: 'Email address is required' });
    }
    
    // Check if rule exists
    const [existingRule] = await db.query(
      'SELECT * FROM Blacklist WHERE ID_Blacklist = ?',
      [id]
    );
    
    if (existingRule.length === 0) {
      return res.status(404).json({ message: 'Filter rule not found' });
    }

    if (!isAdminUser(req) && String(existingRule[0].ID_Utilisateur) !== String(req.userData.userId)) {
      return res.status(403).json({ message: 'Forbidden' });
    }
    
    // Check for duplicate (if the email changed)
    if (existingRule[0].Email !== sender_email) {
      const [duplicateCheck] = isAdminUser(req)
        ? await db.query(
            'SELECT * FROM Blacklist WHERE Email = ? AND ID_Blacklist != ? AND ID_Utilisateur IS NULL',
            [sender_email, id]
          )
        : await db.query(
            'SELECT * FROM Blacklist WHERE Email = ? AND ID_Blacklist != ? AND ID_Utilisateur = ?',
            [sender_email, id, req.userData.userId]
          );
      
      if (duplicateCheck.length > 0) {
        return res.status(400).json({ message: 'This email is already in the blocklist' });
      }
    }
    
    // Update the rule
    await db.query(
      'UPDATE Blacklist SET Email = ?, updated_at = NOW() WHERE ID_Blacklist = ?',
      [sender_email, id]
    );
    
    // Return the updated rule
    const [updatedRule] = await db.query(
      'SELECT * FROM Blacklist WHERE ID_Blacklist = ?',
      [id]
    );
    
    res.json(updatedRule[0]);
  } catch (error) {
    console.error('Error updating filter rule:', error);
    res.status(500).json({ message: 'Server error while updating filter rule' });
  }
};

// Delete a filter rule
exports.deleteFilterRule = async (req, res) => {
  try {
    await ensureBlacklistUserColumn();

    const { id } = req.params;
    
    // Check if rule exists
    const [existingRule] = await db.query(
      'SELECT * FROM Blacklist WHERE ID_Blacklist = ?',
      [id]
    );
    
    if (existingRule.length === 0) {
      return res.status(404).json({ message: 'Filter rule not found' });
    }

    if (!isAdminUser(req) && String(existingRule[0].ID_Utilisateur) !== String(req.userData.userId)) {
      return res.status(403).json({ message: 'Forbidden' });
    }
    
    // Delete the rule
    await db.query('DELETE FROM Blacklist WHERE ID_Blacklist = ?', [id]);
    
    res.status(204).end();
  } catch (error) {
    console.error('Error deleting filter rule:', error);
    res.status(500).json({ message: 'Server error while deleting filter rule' });
  }
};