import React, { useState } from 'react';
import { Card, CardContent, Switch, IconButton, TextField, Button, Collapse } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import WarningDialog from './WarningDialog';

const FeatureCard = ({ feature, onSave, onToggleChange, onNameChange }) => {
  const [expanded, setExpanded] = useState(false);
  const [localFeature, setLocalFeature] = useState(feature);
  const [warningOpen, setWarningOpen] = useState(false);

  const handleToggle = (event) => {
    if (localFeature.children && localFeature.children.length > 0) {
      // Show warning if toggling a feature that has children
      setWarningOpen(true);
    } else {
      const newValue = event.target.checked;
      setLocalFeature({ ...localFeature, is_enabled: newValue });
      onToggleChange(localFeature.id, newValue);
    }
  };

  const handleConfirmWarning = () => {
    setWarningOpen(false);
    const newValue = !localFeature.is_enabled;
    setLocalFeature({ ...localFeature, is_enabled: newValue });
    onToggleChange(localFeature.id, newValue);
  };

  const handleCancelWarning = () => {
    setWarningOpen(false);
  };

  const handleNameChange = (e) => {
    const newName = e.target.value;
    setLocalFeature({ ...localFeature, name: newName });
    onNameChange(localFeature.id, newName);
  };

  return (
    <Card variant="outlined" sx={{ margin: '1rem' }}>
      <CardContent>
        <TextField label="Feature Name" value={localFeature.name} onChange={handleNameChange} variant="standard" fullWidth />
        <Switch checked={localFeature.is_enabled} onChange={handleToggle} />
        {localFeature.children && localFeature.children.length > 0 && (
          <IconButton onClick={() => setExpanded(!expanded)}>
            <ExpandMoreIcon />
          </IconButton>
        )}
        <Button variant="contained" onClick={() => onSave(localFeature)}>Save</Button>
      </CardContent>
      {localFeature.children && localFeature.children.length > 0 && (
        <Collapse in={expanded}>
          {localFeature.children.map(child => (
            <FeatureCard
              key={child.id}
              feature={child}
              onSave={onSave}
              onToggleChange={onToggleChange}
              onNameChange={onNameChange}
            />
          ))}
        </Collapse>
      )}
      <WarningDialog open={warningOpen} onConfirm={handleConfirmWarning} onCancel={handleCancelWarning} message="Toggling this feature will affect all child features. Do you want to proceed?" />
    </Card>
  );
};

export default FeatureCard;
