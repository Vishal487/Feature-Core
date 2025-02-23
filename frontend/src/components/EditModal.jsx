import { useState, useEffect } from "react";
import { Modal, Button, MenuItem, Box, TextField, FormControlLabel, Select, Input, Switch, Alert } from "@mui/material";
import { fetchAllFeatures, updateFeature } from '../services/api';

const editModalStyle = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: 400,
  bgcolor: 'background.paper',
  boxShadow: 24,
  p: 4,
};

const EditFeatureModal = ({ feature, open, onClose, onSave }) => {
  const [name, setName] = useState(feature.name);
  const [isEnabled, setIsEnabled] = useState(feature.is_enabled);
  const [parentId, setParentId] = useState(feature.parent_id);
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
      feature.name = name;
      feature.is_enabled = isEnabled;
      feature.parent_id = parentId;
      // await updateFeature(feature.id, feature);
      await onSave();
      onClose();
      // loadFeatures(); // Ensure UI updates correctly
    } catch (err) {
      setError(err.response?.data?.detail || 'Error updating feature');
    }
  };

  return (
    <Modal title="Edit Feature" open={open} onClose={onClose}>
      <Box sx={editModalStyle}>
        <TextField required label="Feature Name" value={name} onChange={(e) => setName(e.target.value)} fullWidth margin="normal" />
        <FormControlLabel control={<Switch checked={isEnabled} onChange={(e) => setIsEnabled(e.target.checked)} />} label="Enabled" />
        <TextField label="Parent Feature" select fullWidth margin="normal" value={parentId} onChange={(e) => setParentId(e.target.value)} >
          <MenuItem value="">None</MenuItem>
          {topLevelFeatures.map(feature => (
            <MenuItem key={feature.id} value={feature.id}>{feature.name}</MenuItem>
          ))}
        </TextField>
        {/* {error && <Box sx={{ color: 'red', my: 1 }}>{error}</Box>} */}
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button onClick={onClose} sx={{ mr: 1 }}>Cancel</Button>
          <Button variant="contained" onClick={handleSubmit}>Save</Button>
        </Box>
      </Box>
    </Modal>
  );
};

export default EditFeatureModal;
