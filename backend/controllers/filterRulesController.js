const db = require('../config/db');

// Get all filter rules
exports.getFilterRules = async (req, res) => {
  try {
    const [rules] = await db.query(
      'SELECT * FROM Blacklist ORDER BY created_at DESC'
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
    const [rules] = await db.query(
      'SELECT * FROM Blacklist WHERE ID_Blacklist = ?',
      [req.params.id]
    );
    
    if (rules.length === 0) {
      return res.status(404).json({ message: 'Filter rule not found' });
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
    const { sender_email } = req.body;
    
    // Validate input
    if (!sender_email) {
      return res.status(400).json({ message: 'Email address is required' });
    }
    
    // Check for duplicate
    const [existingRules] = await db.query(
      'SELECT * FROM Blacklist WHERE Email = ?',
      [sender_email]
    );
    
    if (existingRules.length > 0) {
      return res.status(400).json({ message: 'This email is already in the blocklist' });
    }
    
    // Insert rule
    const [result] = await db.query(
      'INSERT INTO Blacklist (Email) VALUES (?)',
      [sender_email]
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
    
    // Check for duplicate (if the email changed)
    if (existingRule[0].Email !== sender_email) {
      const [duplicateCheck] = await db.query(
        'SELECT * FROM Blacklist WHERE Email = ? AND ID_Blacklist != ?',
        [sender_email, id]
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
    const { id } = req.params;
    
    // Check if rule exists
    const [existingRule] = await db.query(
      'SELECT * FROM Blacklist WHERE ID_Blacklist = ?',
      [id]
    );
    
    if (existingRule.length === 0) {
      return res.status(404).json({ message: 'Filter rule not found' });
    }
    
    // Delete the rule
    await db.query('DELETE FROM Blacklist WHERE ID_Blacklist = ?', [id]);
    
    res.status(204).end();
  } catch (error) {
    console.error('Error deleting filter rule:', error);
    res.status(500).json({ message: 'Server error while deleting filter rule' });
  }
};