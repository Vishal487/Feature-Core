import React, { useEffect, useState } from 'react';
import { Button, CircularProgress, Box } from '@mui/material';
import { getFeatures } from '../../services/api';
import FeatureItem from './FeatureItem';
import CreateFeatureModal from '../CreateFeatureModal';

const FeatureList = () => {
  const [features, setFeatures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  const loadFeatures = async () => {
    try {
      const { data } = await getFeatures();
      setFeatures(data.features);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFeatures();
  }, []);

  if (loading) return <CircularProgress />;

  return (
    <Box sx={{ p: 4 }}>
      <Box display="flex" justifyContent="flex-end" mb={4}>
        <Button 
          variant="contained" 
          onClick={() => setModalOpen(true)}
        >
          Create New Feature
        </Button>
      </Box>

      {features.map(feature => (
        <FeatureItem
          key={feature.id}
          feature={feature}
          onSave={async (id, data) => {
            try {
              await updateFeature(id, data);
              loadFeatures();
            } catch (error) {
              console.error('Update failed:', error);
            }
          }}
        />
      ))}
      
      <CreateFeatureModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSuccess={loadFeatures}
      />
    </Box>
  );
};

export default FeatureList;