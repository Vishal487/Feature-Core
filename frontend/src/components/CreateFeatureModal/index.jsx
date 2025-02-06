import React, { useState } from 'react';
import {
  Modal,
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  Button,
  Typography
} from '@mui/material';
import { createFeature, getFeatures } from '../../services/api';

const CreateFeatureModal = ({ open, onClose, onSuccess }) => {
  const [name, setName] = useState('');
  const [enabled, setEnabled] = useState(false);
  const [parentId, setParentId] = useState('');
  const [parents, setParents] = useState([]);
  const [error, setError] = useState('');

  const loadParents = async () => {
    const { data } = await getFeatures();
    setParents(data.features.filter(f => !f.parent_id));
  };

  const handleSubmit = async () => {
    try {
      await createFeature({
        name,
        is_enabled: enabled,
        parent_id: parentId || null
      });
      onSuccess();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Creation failed');
    }
  };

  return (
    <Modal open={open} onClose={onClose}>
      <Box sx={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        bgcolor: 'background.paper',
        boxShadow: 24,
        p: 4,
        minWidth: 400
      }}>
        <Typography variant="h6" mb={2}>Create New Feature</Typography>
        
        <TextField
          label="Name"
          fullWidth
          value={name}
          onChange={(e) => setName(e.target.value)}
          sx={{ mb: 2 }}
        />
        
        <Box display="flex" alignItems="center" mb={2}>
          <Typography>Enabled</Typography>
          <Switch 
            checked={enabled} 
            onChange={(e) => setEnabled(e.target.checked)} 
          />
        </Box>

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Parent Feature</InputLabel>
          <Select
            value={parentId}
            label="Parent Feature"
            onChange={(e) => setParentId(e.target.value)}
            onOpen={loadParents}
          >
            <MenuItem value=""><em>None</em></MenuItem>
            {parents.map(parent => (
              <MenuItem key={parent.id} value={parent.id}>
                {parent.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {error && <Typography color="error" sx={{ mb: 2 }}>{error}</Typography>}
        
        <Box display="flex" justifyContent="flex-end" gap={2}>
          <Button onClick={onClose}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleSubmit}
            disabled={!name}
          >
            Create
          </Button>
        </Box>
      </Box>
    </Modal>
  );
};

export default CreateFeatureModal;