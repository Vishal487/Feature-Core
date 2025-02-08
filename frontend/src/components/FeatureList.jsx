import React, { useState } from "react";
import { Grid, Fab, TextField, Box } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import FeatureCard from "./FeatureCard";

const FeatureList = ({
  features,
  onSaveFeature,
  onToggleChange,
  onNameChange,
  onCreateFeature,
  onDelete
}) => {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredFeatures = features.filter(
    (feature) =>
      feature.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (feature.children &&
        feature.children.some((child) =>
          child.name.toLowerCase().includes(searchQuery.toLowerCase())
        ))
  );

  return (
    <Box style={{ position: "relative", padding: "1rem" }}>
      {/* Search Input */}
      <Box
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1rem",
        }}
      >
        <TextField
          variant="outlined"
          size="small"
          label="Search..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            maxWidth: "300px",
            alignSelf: "flex-start",
          }}
        />
        {/* Add Button */}
        <Fab
          color="primary"
          aria-label="add"
          onClick={onCreateFeature}
          style={{
            position: "relative",
            alignSelf: "flex-end",
          }}
        >
          <AddIcon />
        </Fab>
      </Box>
      {/* Feature Cards */}
      <Grid container spacing={2}>
        {filteredFeatures.map((feature) => (
          <Grid item xs={12} key={feature.id}>
            <FeatureCard
              feature={feature}
              onSave={onSaveFeature}
              onToggleChange={onToggleChange}
              onNameChange={onNameChange}
              onDelete={onDelete}
            />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default FeatureList;
