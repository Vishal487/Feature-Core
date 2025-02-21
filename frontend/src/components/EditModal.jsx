import { useState } from "react";
import { Modal, Button, MenuItem, Box, TextField, FormControlLabel, Select, Input, Switch, Alert } from "@mui/material";


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
    const [parentId, setParentId] = useState('');
    const [topLevelFeatures, setTopLevelFeatures] = useState([]);

    return (
        <Modal title="Edit Feature" open={open} onClose={onClose}>
        <Box sx={editModalStyle}>
          <TextField required label="Feature Name" value={name} onChange={(e) => setName(e.target.value)} fullWidth margin="normal" />
          <FormControlLabel control={<Switch checked={isEnabled} onChange={(e) => setIsEnabled(e.target.checked)}  />} label="Enabled" />
          <TextField label="Parent Feature" select fullWidth margin="normal" value={parentId} onChange={(e) => setParentId(e.target.value)} >
            <MenuItem value="">None</MenuItem>
            {topLevelFeatures.map(feature => (
              <MenuItem key={feature.id} value={feature.id}>{feature.name}</MenuItem>
            ))}
          </TextField>
          {/* {error && <Box sx={{ color: 'red', my: 1 }}>{error}</Box>} */}
          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button onClick={onClose} sx={{ mr: 1 }}>Cancel</Button>
            <Button  variant="contained" >Save</Button>
          </Box>
        </Box>
      </Modal>
    );
};

export default EditFeatureModal;
