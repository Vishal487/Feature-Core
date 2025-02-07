import React, { useEffect, useState } from 'react';
import { Container, Typography } from '@mui/material';
import FeatureList from './components/FeatureList';
import FeatureModal from './components/FeatureModal';
import { fetchAllFeatures, updateFeature } from './services/api';

const App = () => {
  const [features, setFeatures] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);

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
      await updateFeature(feature.id, feature);
      loadFeatures(); // Ensure UI updates correctly
    } catch (err) {
      console.error(err);
    }
  };

  const handleToggleChange = async (featureId, newValue) => {
    try {
      const updatedFeatures = features.map(f =>
        f.id === featureId ? { ...f, is_enabled: newValue } : f
      );
      setFeatures(updatedFeatures);
      // await updateFeature(featureId, { is_enabled: newValue });
      // loadFeatures(); // Ensure correct state
    } catch (err) {
      console.error(err);
    }
  };

  const handleNameChange = (featureId, newName) => {
    setFeatures(prevFeatures =>
      prevFeatures.map(f => (f.id === featureId ? { ...f, name: newName } : f))
    );
  };

  const handleCreateFeature = () => {
    setModalOpen(true);
  };

  const handleFeatureCreated = () => {
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
