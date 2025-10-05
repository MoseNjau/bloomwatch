// ========================================
// NASA BLOOMWATCH - GOOGLE EARTH ENGINE CODE EXAMPLES
// Complete scripts for bloom detection and visualization
// ========================================

// SCRIPT 1: BASIC NDVI/EVI VISUALIZATION
// Copy-paste this into Google Earth Engine Code Editor
// ========================================

// 1️⃣ Load MODIS data for 2023
var dataset = ee.ImageCollection('MODIS/061/MOD13Q1')
  .filterDate('2023-01-01', '2023-12-31')
  .select(['NDVI', 'EVI']);

// Apply scale factor (MODIS vegetation indices are scaled by 10000)
var scaledDataset = dataset.map(function(image) {
  return image.multiply(0.0001).copyProperties(image, image.propertyNames());
});

// Compute yearly mean NDVI and EVI
var meanNDVI = scaledDataset.select('NDVI').mean();
var meanEVI = scaledDataset.select('EVI').mean();

// Visualization parameters
var visParams = {
  min: 0, 
  max: 1, 
  palette: ['brown', 'yellow', 'green']
};

// Center the map (change coordinates for your area of interest)
Map.setCenter(45.3, 2.0, 5); // Somalia region example

// Add layers to map
Map.addLayer(meanNDVI, visParams, 'Mean NDVI (2023)');
Map.addLayer(meanEVI, visParams, 'Mean EVI (2023)');

// Peak NDVI (when vegetation was highest)
var peakNDVI = scaledDataset.qualityMosaic('NDVI').select('NDVI');
Map.addLayer(peakNDVI, visParams, 'Peak NDVI (2023)');

print('Dataset loaded successfully!');
print('Image count:', dataset.size());

// ========================================
// SCRIPT 2: TIME SERIES ANALYSIS FOR BLOOM DETECTION
// ========================================

// Define region of interest (change coordinates)
var roi = ee.Geometry.Point([45.3, 2.0]); // Near Mogadishu
Map.centerObject(roi, 8);
Map.addLayer(roi, {color: 'red'}, 'ROI Point');

// Create NDVI time series chart
var ndviChart = ui.Chart.image.series({
  imageCollection: scaledDataset.select('NDVI'),
  region: roi,
  reducer: ee.Reducer.mean(),
  scale: 250
}).setOptions({
  title: 'NDVI Time Series - 2023 (Bloom Detection)',
  vAxis: {title: 'NDVI'},
  hAxis: {title: 'Date'},
  lineWidth: 2,
  pointSize: 4,
  colors: ['green']
});

print(ndviChart);

// Create EVI time series chart
var eviChart = ui.Chart.image.series({
  imageCollection: scaledDataset.select('EVI'),
  region: roi,
  reducer: ee.Reducer.mean(),
  scale: 250
}).setOptions({
  title: 'EVI Time Series - 2023 (Enhanced Vegetation Index)',
  vAxis: {title: 'EVI'},
  hAxis: {title: 'Date'},
  lineWidth: 2,
  pointSize: 4,
  colors: ['blue']
});

print(eviChart);

// ========================================
// SCRIPT 3: BLOOM DETECTION ALGORITHM
// ========================================

// Function to detect bloom events
function detectBlooms(collection, roi) {
  // Define bloom thresholds
  var ndviThreshold = 0.4;
  var eviThreshold = 0.3;
  
  // Create bloom mask
  var bloomCollection = collection.map(function(image) {
    var ndvi = image.select('NDVI');
    var evi = image.select('EVI');
    
    // Bloom probability based on both indices
    var bloomMask = ndvi.gt(ndviThreshold).and(evi.gt(eviThreshold));
    var bloomProbability = ndvi.add(evi).divide(2).multiply(bloomMask);
    
    return image.addBands(bloomProbability.rename('bloom_probability'))
                .addBands(bloomMask.rename('bloom_mask'));
  });
  
  return bloomCollection;
}

// Apply bloom detection
var bloomData = detectBlooms(scaledDataset, roi);

// Visualize bloom probability
var bloomVis = {
  min: 0,
  max: 1,
  palette: ['white', 'yellow', 'orange', 'red']
};

var maxBloomProbability = bloomData.select('bloom_probability').max();
Map.addLayer(maxBloomProbability, bloomVis, 'Max Bloom Probability');

// Create bloom probability time series
var bloomChart = ui.Chart.image.series({
  imageCollection: bloomData.select('bloom_probability'),
  region: roi,
  reducer: ee.Reducer.mean(),
  scale: 250
}).setOptions({
  title: 'Bloom Probability Time Series - 2023',
  vAxis: {title: 'Bloom Probability'},
  hAxis: {title: 'Date'},
  lineWidth: 3,
  pointSize: 5,
  colors: ['red']
});

print(bloomChart);

// ========================================
// SCRIPT 4: PHENOLOGY ANALYSIS (Start/Peak/End of Season)
// ========================================

// Function to calculate phenology metrics
function calculatePhenology(collection, roi) {
  // Sort collection by date
  var sortedCollection = collection.sort('system:time_start');
  
  // Calculate statistics
  var maxNDVI = sortedCollection.select('NDVI').max();
  var minNDVI = sortedCollection.select('NDVI').min();
  var meanNDVI = sortedCollection.select('NDVI').mean();
  
  // Define thresholds for phenology phases
  var amplitude = maxNDVI.subtract(minNDVI);
  var sosThreshold = minNDVI.add(amplitude.multiply(0.2)); // Start of Season: 20% of amplitude
  var eosThreshold = minNDVI.add(amplitude.multiply(0.2)); // End of Season: 20% of amplitude
  
  // Find Start of Season (first time NDVI crosses threshold)
  var sosCollection = sortedCollection.map(function(image) {
    var ndvi = image.select('NDVI');
    var isAboveThreshold = ndvi.gt(sosThreshold);
    return image.set('above_sos_threshold', isAboveThreshold);
  });
  
  // Get date of peak NDVI
  var peakImage = sortedCollection.qualityMosaic('NDVI');
  var peakDate = ee.Date(peakImage.get('system:time_start'));
  
  return {
    'max_ndvi': maxNDVI,
    'min_ndvi': minNDVI,
    'amplitude': amplitude,
    'peak_date': peakDate,
    'sos_threshold': sosThreshold
  };
}

// Calculate phenology for ROI
var phenologyMetrics = calculatePhenology(scaledDataset, roi);

// Display results
print('Phenology Analysis Results:');
print('Peak Date:', phenologyMetrics.peak_date);
print('NDVI Amplitude:', phenologyMetrics.amplitude);

// Visualize phenology
Map.addLayer(phenologyMetrics.max_ndvi, visParams, 'Peak NDVI (Phenology)');
Map.addLayer(phenologyMetrics.amplitude, {min: 0, max: 0.5, palette: ['white', 'green']}, 'NDVI Amplitude');

// ========================================
// SCRIPT 5: MULTI-YEAR BLOOM COMPARISON
// ========================================

// Load data for multiple years
var dataset2022 = ee.ImageCollection('MODIS/061/MOD13Q1')
  .filterDate('2022-01-01', '2022-12-31')
  .select(['NDVI', 'EVI'])
  .map(function(image) {
    return image.multiply(0.0001).copyProperties(image, image.propertyNames());
  });

var dataset2023 = ee.ImageCollection('MODIS/061/MOD13Q1')
  .filterDate('2023-01-01', '2023-12-31')
  .select(['NDVI', 'EVI'])
  .map(function(image) {
    return image.multiply(0.0001).copyProperties(image, image.propertyNames());
  });

// Compare mean NDVI between years
var meanNDVI2022 = dataset2022.select('NDVI').mean();
var meanNDVI2023 = dataset2023.select('NDVI').mean();

// Calculate difference
var ndviDifference = meanNDVI2023.subtract(meanNDVI2022);

// Visualize comparison
var diffVis = {
  min: -0.3,
  max: 0.3,
  palette: ['red', 'white', 'green']
};

Map.addLayer(ndviDifference, diffVis, 'NDVI Change (2023 - 2022)');

// Time series comparison
var roi2 = ee.Geometry.Point([45.3, 2.0]);

var comparisonChart = ui.Chart.image.series({
  imageCollection: dataset2022.select('NDVI').merge(dataset2023.select('NDVI')),
  region: roi2,
  reducer: ee.Reducer.mean(),
  scale: 250
}).setOptions({
  title: 'NDVI Comparison: 2022 vs 2023',
  vAxis: {title: 'NDVI'},
  hAxis: {title: 'Date'},
  lineWidth: 2,
  pointSize: 3
});

print(comparisonChart);

// ========================================
// SCRIPT 6: REGIONAL BLOOM MAPPING
// ========================================

// Define a larger region (bounding box)
var region = ee.Geometry.Rectangle([44.0, 1.0, 46.0, 3.0]); // Somalia region
Map.centerObject(region, 7);

// Load recent data
var recentData = ee.ImageCollection('MODIS/061/MOD13Q1')
  .filterDate('2023-06-01', '2023-08-31') // Summer bloom period
  .filterBounds(region)
  .select(['NDVI', 'EVI'])
  .map(function(image) {
    return image.multiply(0.0001).copyProperties(image, image.propertyNames());
  });

// Calculate bloom intensity map
var bloomIntensity = recentData.map(function(image) {
  var ndvi = image.select('NDVI');
  var evi = image.select('EVI');
  
  // Combined bloom intensity
  var intensity = ndvi.add(evi).divide(2);
  
  // Apply bloom threshold
  var isBloom = ndvi.gt(0.4).and(evi.gt(0.3));
  var bloomValue = intensity.multiply(isBloom);
  
  return image.addBands(bloomValue.rename('bloom_intensity'));
}).select('bloom_intensity').max();

// Visualize regional blooms
var bloomIntensityVis = {
  min: 0,
  max: 1,
  palette: ['white', 'lightgreen', 'green', 'darkgreen']
};

Map.addLayer(bloomIntensity, bloomIntensityVis, 'Regional Bloom Intensity');

// Add region boundary
Map.addLayer(region, {color: 'blue', fillColor: '00000000'}, 'Analysis Region');

// ========================================
// SCRIPT 7: EXPORT DATA FOR FURTHER ANALYSIS
// ========================================

// Export mean NDVI for 2023
Export.image.toDrive({
  image: meanNDVI,
  description: 'BloomWatch_MeanNDVI_2023',
  region: region,
  scale: 250,
  maxPixels: 1e13,
  fileFormat: 'GeoTIFF'
});

// Export bloom intensity map
Export.image.toDrive({
  image: bloomIntensity,
  description: 'BloomWatch_BloomIntensity_Summer2023',
  region: region,
  scale: 250,
  maxPixels: 1e13,
  fileFormat: 'GeoTIFF'
});

// Export time series data as CSV
var timeSeriesData = scaledDataset.select(['NDVI', 'EVI']).getRegion(roi, 250);
Export.table.toDrive({
  collection: ee.FeatureCollection(timeSeriesData),
  description: 'BloomWatch_TimeSeries_2023',
  fileFormat: 'CSV'
});

print('Export tasks created! Check the Tasks tab to run them.');

// ========================================
// SCRIPT 8: ADVANCED BLOOM DETECTION WITH SMOOTHING
// ========================================

// Function to apply Savitzky-Golay smoothing (approximation)
function smoothTimeSeries(collection) {
  var list = collection.toList(collection.size());
  var smoothed = ee.ImageCollection([]);
  
  var size = collection.size();
  
  for (var i = 2; i < size.subtract(2).getInfo(); i++) {
    var prev2 = ee.Image(list.get(i-2));
    var prev1 = ee.Image(list.get(i-1));
    var current = ee.Image(list.get(i));
    var next1 = ee.Image(list.get(i+1));
    var next2 = ee.Image(list.get(i+2));
    
    // Simple 5-point smoothing (Savitzky-Golay approximation)
    var smoothedImage = prev2.multiply(-3)
                           .add(prev1.multiply(12))
                           .add(current.multiply(17))
                           .add(next1.multiply(12))
                           .add(next2.multiply(-3))
                           .divide(35);
    
    smoothed = smoothed.merge(ee.ImageCollection([smoothedImage.copyProperties(current)]));
  }
  
  return smoothed;
}

// Apply smoothing to detect subtle bloom patterns
var smoothedCollection = smoothTimeSeries(scaledDataset);

// Create smoothed time series chart
var smoothedChart = ui.Chart.image.series({
  imageCollection: smoothedCollection.select('NDVI'),
  region: roi,
  reducer: ee.Reducer.mean(),
  scale: 250
}).setOptions({
  title: 'Smoothed NDVI Time Series - Advanced Bloom Detection',
  vAxis: {title: 'NDVI (Smoothed)'},
  hAxis: {title: 'Date'},
  lineWidth: 3,
  pointSize: 0,
  colors: ['darkgreen']
});

print(smoothedChart);

// ========================================
// USAGE INSTRUCTIONS
// ========================================

print('=== BLOOMWATCH GOOGLE EARTH ENGINE SCRIPTS ===');
print('');
print('INSTRUCTIONS:');
print('1. Copy each script section into GEE Code Editor');
print('2. Modify coordinates for your area of interest');
print('3. Adjust date ranges as needed');
print('4. Run scripts to visualize bloom patterns');
print('');
print('KEY OUTPUTS:');
print('- NDVI/EVI time series charts');
print('- Bloom probability maps');
print('- Phenology analysis results');
print('- Regional bloom intensity maps');
print('- Exportable data for backend integration');
print('');
print('NEXT STEPS:');
print('- Use exported data in BloomWatch backend');
print('- Integrate with species identification');
print('- Connect to bee farmer dashboard');
print('- Implement real-time alerts');

// ========================================
// BEE FARMER SPECIFIC ANALYSIS
// ========================================

// Function to calculate nectar flow potential
function calculateNectarFlow(collection, roi) {
  return collection.map(function(image) {
    var ndvi = image.select('NDVI');
    var evi = image.select('EVI');
    
    // Nectar flow estimation based on vegetation health
    var nectarPotential = ndvi.multiply(0.6).add(evi.multiply(0.4));
    
    // Classify nectar flow levels
    var nectarFlow = ee.Image(0)
      .where(nectarPotential.lt(0.3), 1) // Minimal
      .where(nectarPotential.gte(0.3).and(nectarPotential.lt(0.5)), 2) // Light
      .where(nectarPotential.gte(0.5).and(nectarPotential.lt(0.7)), 3) // Moderate
      .where(nectarPotential.gte(0.7), 4); // Heavy
    
    return image.addBands(nectarFlow.rename('nectar_flow'))
                .addBands(nectarPotential.rename('nectar_potential'));
  });
}

// Apply nectar flow analysis
var nectarData = calculateNectarFlow(scaledDataset, roi);

// Visualize nectar flow potential
var nectarVis = {
  min: 1,
  max: 4,
  palette: ['red', 'yellow', 'lightgreen', 'darkgreen']
};

var maxNectarFlow = nectarData.select('nectar_flow').mode();
Map.addLayer(maxNectarFlow, nectarVis, 'Nectar Flow Classification');

// Create nectar flow time series for bee farmers
var nectarChart = ui.Chart.image.series({
  imageCollection: nectarData.select('nectar_potential'),
  region: roi,
  reducer: ee.Reducer.mean(),
  scale: 250
}).setOptions({
  title: 'Nectar Flow Potential - Bee Farmer Analysis',
  vAxis: {title: 'Nectar Flow Potential'},
  hAxis: {title: 'Date'},
  lineWidth: 3,
  pointSize: 4,
  colors: ['orange']
});

print(nectarChart);

print('🐝 BEE FARMER INSIGHTS:');
print('- Green areas = High nectar flow (move hives here)');
print('- Yellow areas = Moderate nectar flow');
print('- Red areas = Low nectar flow (avoid)');
print('- Use time series to plan hive movements');

// ========================================
// END OF SCRIPTS
// ========================================
