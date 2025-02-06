import React, { useEffect, useState } from 'react';
import { Container, Typography } from '@mui/material';
import FeatureList from './components/FeatureList';
import FeatureModal from './components/FeatureModal';
import { fetchAllFeatures, updateFeature } from './services/api';

const App = () => {
  const [features, setFeatures] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);

  // Load all features on component mount or refresh
  const loadFeatures = async () => {
    try {
      const data = await fetchAllFeatures();
      setFeatures(data.features);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadFeatures();
  }, []);

  const handleSaveFeature = async (feature) => {
    try {
      // Prepare payload from feature object and call update API
      const payload = {
        name: feature.name,
        is_enabled: feature.is_enabled,
        parent_id: feature.parent_id,
      };
      const updatedFeature = await updateFeature(feature.id, payload);
      // Refresh the features list after save
      loadFeatures();
    } catch (err) {
      console.error(err);
      // Optionally show an error message
    }
  };

  const handleToggleChange = (featureId, newStatus) => {
    // Update local state immediately for responsive UI
    setFeatures((prevFeatures) =>
      prevFeatures.map((feature) =>
        feature.id === featureId ? { ...feature, is_enabled: newStatus } : feature
      )
    );
  };

  const handleNameChange = (featureId, newName) => {
    setFeatures((prevFeatures) =>
      prevFeatures.map((feature) =>
        feature.id === featureId ? { ...feature, name: newName } : feature
      )
    );
  };

  const handleCreateFeature = () => {
    setModalOpen(true);
  };

  const handleFeatureCreated = (newFeature) => {
    // Optionally add the new feature locally or simply reload the list
    loadFeatures();
  };

  return (
    <Container>
      <Typography variant="h4" align="center" sx={{ mt: 4, mb: 2 }}>
        Feature Flags
      </Typography>
      <FeatureList
        features={features}
        onSaveFeature={handleSaveFeature}
        onToggleChange={handleToggleChange}
        onNameChange={handleNameChange}
        onCreateFeature={handleCreateFeature}
      />
      <FeatureModal open={modalOpen} onClose={() => setModalOpen(false)} onCreated={handleFeatureCreated} />
    </Container>
  );
};

export default App;
