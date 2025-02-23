import React, { useState, useEffect } from 'react';
import { Card, Fab, CardContent, Switch, IconButton, TextField, Button, Collapse, Grid, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import DeleteIcon from '@mui/icons-material/Delete';
import WarningDialog from './WarningDialog';
import EditFeatureModal from "./EditModal";
import EditIcon from '@mui/icons-material/Edit';
import { Modal, Box, FormControlLabel,  MenuItem } from '@mui/material';


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

const FeatureCard = ({ feature, onSave, onToggleChange, onNameChange, onDelete }) => {
  const [expanded, setExpanded] = useState(false);
  const [localFeature, setLocalFeature] = useState(feature);
  const [warningOpen, setWarningOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);

  useEffect(() => {
    setLocalFeature(feature); // Sync with updated props
  }, [feature]);

  const handleToggle = () => {
    if (feature.children && feature.children.length > 0) {
      setWarningOpen(true);
    } else {
      toggleFeature();
    }
  };

  const toggleFeature = () => {
    const newValue = !localFeature.is_enabled;
    setLocalFeature(prev => ({ ...prev, is_enabled: newValue }));
    onToggleChange && onToggleChange(localFeature.id, newValue); // Ensure function exists
    setHasChanges(true);
  };

  const handleConfirmWarning = () => {
    setWarningOpen(false);
    toggleFeature();
  };

  const handleCancelWarning = () => {
    setWarningOpen(false);
  };

  const handleNameChange = (e) => {
    const newName = e.target.value;
    setLocalFeature(prev => ({ ...prev, name: newName }));
    onNameChange && onNameChange(localFeature.id, newName); // Ensure function exists
    setHasChanges(true);
  };

  const handleSave = () => {
    onSave && onSave(localFeature);
    setHasChanges(false);
  };

  const handleDelete = () => {
    setDeleteConfirmOpen(true);
  };

  const handleConfirmDelete = async () => {
    setDeleteConfirmOpen(false);
    onDelete && (await onDelete(localFeature.id)); // Call delete handler
  };

  const handleCancelDelete = () => {
    setDeleteConfirmOpen(false);
  };

  const handleEdit = () => {
    setEditModalOpen(true)
  }

  return (
    <Card variant="outlined" sx={{ margin: '1rem' }}>
      <CardContent>
        <Grid container alignItems="center" spacing={2}>
          {/* Expand Button (or empty space if not present) */}
          <Grid item>
            {feature.children && feature.children.length > 0 ? (
              <IconButton onClick={() => setExpanded(!expanded)}>
                <ExpandMoreIcon />
              </IconButton>
            ) : (
              <div style={{ width: '40px' }}></div> // Empty space for alignment
            )}
          </Grid>

          {/* Feature Name Input */}
          <Grid item xs>
            <TextField
              label="Feature Name"
              value={localFeature.name}
              onChange={handleNameChange}
              variant="standard"
              fullWidth
              required
            />
          </Grid>

          {/* Toggle Button */}
          <Grid item>
            <Switch checked={localFeature.is_enabled} onChange={handleToggle} />
          </Grid>

          {/* Save Button */}
          <Grid item>
            <Button variant="contained" onClick={handleSave} disabled={!hasChanges || !localFeature.name}>
              Save
            </Button>
          </Grid>

          {/* Edit Button */}
          <Grid item>
            <IconButton variant="contained" color="secondary" onClick={handleEdit}>
              <EditIcon />
            </IconButton>
          </Grid>

          {/* Delete Button */}
          <Grid item>
            <IconButton color="error" onClick={handleDelete}>
              <DeleteIcon />
            </IconButton>
          </Grid>
        </Grid>
      </CardContent>

      {/* Collapsible Children */}
      {feature.children && feature.children.length > 0 && (
        <Collapse in={expanded}>
          {feature.children.map(child => (
            <FeatureCard
              key={child.id}
              feature={child}
              onSave={() => handleSave()}
              onToggleChange={onToggleChange}
              onNameChange={onNameChange}
              onDelete={onDelete}
            />
          ))}
        </Collapse>
      )}

      {/* Warning Dialog */}
      <WarningDialog open={warningOpen} onConfirm={handleConfirmWarning} onCancel={handleCancelWarning} message="Toggling this feature will affect all child features. Do you want to proceed?" />

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onClose={handleCancelDelete}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>Are you sure you want to delete this feature? This action cannot be undone.</DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete}>Cancel</Button>
          <Button onClick={handleConfirmDelete} color="error">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* EditModal */}
      {/* <Modal title="Edit Feature" open={editModalOpen} onClose={() => setEditModalOpen(false)}>
        <Box sx={editModalStyle}>
          <TextField required label="Feature Name" value={feature.name}  fullWidth margin="normal" />
          <FormControlLabel control={<Switch checked={feature.is_enabled}  />} label="Enabled" />
          <TextField label="Parent Feature" select fullWidth margin="normal" value={feature.parent_id} >
            <MenuItem value="">None</MenuItem>
            {topLevelFeatures.map(feature => (
              <MenuItem key={feature.id} value={feature.id}>{feature.name}</MenuItem>
            ))}
          </TextField>
          {error && <Box sx={{ color: 'red', my: 1 }}>{error}</Box>}
          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button onClick={() => setEditModalOpen(false)} sx={{ mr: 1 }}>Cancel</Button>
            <Button  variant="contained" >Save</Button>
          </Box>
        </Box>
      </Modal> */}

      <EditFeatureModal 
        feature={localFeature}
        open={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        onSave={() => handleSave()}
      />

    </Card>
  );
};

export default FeatureCard;
