import React from 'react';
import { Grid, Fab } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import FeatureCard from './FeatureCard';

const FeatureList = ({ features, onSaveFeature, onToggleChange, onNameChange, onCreateFeature }) => {
  return (
    <div style={{ position: 'relative', padding: '1rem' }}>
      <Grid container spacing={2}>
        {features.map(feature => (
          <Grid item xs={12} key={feature.id}>
            <FeatureCard feature={feature} onSave={onSaveFeature} onToggleChange={onToggleChange} onNameChange={onNameChange} />
          </Grid>
        ))}
      </Grid>
      <Fab color="primary" aria-label="add" style={{ position: 'fixed', top: '1rem', right: '1rem' }} onClick={onCreateFeature}>
        <AddIcon />
      </Fab>
    </div>
  );
};

export default FeatureList;
