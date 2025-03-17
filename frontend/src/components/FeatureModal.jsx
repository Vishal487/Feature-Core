import React, { useState, useEffect } from 'react';
import { Modal, Box, TextField, Switch, FormControlLabel, Button, MenuItem } from '@mui/material';
import { fetchAllFeatures, createFeature } from '../services/api';

const modalStyle = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: 400,
  bgcolor: 'background.paper',
  boxShadow: 24,
  p: 4,
};

const FeatureModal = ({ open, onClose, onCreated }) => {
  const [name, setName] = useState('');
  const [isEnabled, setIsEnabled] = useState(false);
  const [parentId, setParentId] = useState('');
  const [topLevelFeatures, setTopLevelFeatures] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadTopLevelFeatures = async () => {
      try {
        const data = await fetchAllFeatures();
        const topFeatures = data.features.filter(feature => feature.parent_id === null);
        setTopLevelFeatures(topFeatures);
      } catch (err) {
        console.error(err);
      }
    };
    if (open) loadTopLevelFeatures();
  }, [open]);

  const handleSubmit = async () => {
    try {
      setError(null);
      const payload = { name, is_enabled: isEnabled, parent_id: parentId ? Number(parentId) : null };
      const newFeature = await createFeature(payload);
      onCreated(newFeature);
      onClose();
      setName('');
      setIsEnabled(false);
      setParentId('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error creating feature');
    }
  };

  return (
    <Modal open={open} onClose={onClose}>
      <Box sx={modalStyle}>
        <TextField required label="Feature Name" value={name} onChange={(e) => setName(e.target.value)} fullWidth margin="normal" />
        <FormControlLabel control={<Switch checked={isEnabled} onChange={(e) => setIsEnabled(e.target.checked)} />} label="Enabled" />
        <TextField label="Parent Feature" select fullWidth margin="normal" value={parentId} onChange={(e) => setParentId(e.target.value)}>
          <MenuItem value="">None</MenuItem>
          {topLevelFeatures.map(feature => (
            <MenuItem key={feature.id} value={feature.id}>{feature.name}</MenuItem>
          ))}
        </TextField>
        {error && <Box sx={{ color: 'red', my: 1 }}>{error}</Box>}
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button onClick={onClose} sx={{ mr: 1 }}>Cancel</Button>
          <Button disabled={!name.trim()} variant="contained" onClick={handleSubmit}>Save</Button>
        </Box>
      </Box>
    </Modal>
  );
};

export default FeatureModal;
