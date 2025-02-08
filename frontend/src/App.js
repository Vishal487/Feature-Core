import React, { useEffect, useState } from 'react';
import { Container, Typography, Snackbar, Alert } from '@mui/material';
import FeatureList from './components/FeatureList';
import FeatureModal from './components/FeatureModal';
import { fetchAllFeatures, updateFeature } from './services/api';

const App = () => {
  const [features, setFeatures] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [error, setError] = useState(null); // For storing error messages
  const [snackbarOpen, setSnackbarOpen] = useState(false); // To control Snackbar visibility

  const loadFeatures = async () => {
    try {
      const data = await fetchAllFeatures();
      setFeatures(data.features);
    } catch (err) {
      // console.error(err);
      showErrorSnackbar('Failed to load features.');
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
      // console.error(err);
      showErrorSnackbar('Failed to save feature.');
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
      // console.error(err);
      showErrorSnackbar('Failed to update feature status.');
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

  const showErrorSnackbar = (message) => {
    setError(message);
    setSnackbarOpen(true);
  };

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
    setError(null);
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

      {/* Snackbar for error notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={5000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default App;
