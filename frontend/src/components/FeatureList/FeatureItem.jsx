import React, { useState } from 'react';
import { Box, Typography, Switch, Button, TextField, Collapse } from '@mui/material';
import { ExpandMore, ExpandLess } from '@mui/icons-material';

const FeatureItem = ({ feature, onSave, onToggle }) => {
  const [expanded, setExpanded] = useState(false);
  const [editName, setEditName] = useState(false);
  const [tempName, setTempName] = useState(feature.name);
  const [tempEnabled, setTempEnabled] = useState(feature.is_enabled);

  const handleToggle = () => {
    if (feature.children?.length > 0) {
      alert('Changing this will update all children!');
    }
    setTempEnabled(!tempEnabled);
  };

  return (
    <Box sx={{ ml: 2 }}>
      <Box display="flex" alignItems="center" gap={2}>
        {feature.children?.length > 0 && (
          <Button onClick={() => setExpanded(!expanded)}>
            {expanded ? <ExpandLess /> : <ExpandMore />}
          </Button>
        )}
        
        {editName ? (
          <TextField
            value={tempName}
            onChange={(e) => setTempName(e.target.value)}
            size="small"
          />
        ) : (
          <Typography variant="h6">{feature.name}</Typography>
        )}
        
        <Switch checked={tempEnabled} onChange={handleToggle} />
        <Button
          variant="contained"
          size="small"
          onClick={() => {
            onSave(feature.id, { 
              name: tempName, 
              is_enabled: tempEnabled 
            });
            setEditName(false);
          }}
        >
          Save
        </Button>
        <Button onClick={() => setEditName(!editName)}>
          {editName ? 'Cancel' : 'Edit Name'}
        </Button>
      </Box>

      <Collapse in={expanded}>
        {feature.children?.map(child => (
          <FeatureItem 
            key={child.id}
            feature={child}
            onSave={onSave}
            onToggle={onToggle}
          />
        ))}
      </Collapse>
    </Box>
  );
};

export default FeatureItem;