import React, { useState } from 'react';
import {
  Text,
  View,
  StyleSheet,
  TouchableOpacity,
  Image,
  ScrollView,
  ActivityIndicator,
  Alert,
  Platform,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface AnalysisResult {
  id: string;
  health_status: string;
  issues: string[];
  remedies: string[];
  detailed_analysis: string;
  image_base64: string;
  timestamp: string;
}

export default function Index() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  // Request permissions and pick image
  const pickImage = async () => {
    try {
      // Request permissions
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      
      if (status !== 'granted') {
        Alert.alert(
          'Permission Required',
          'Please allow access to your photo library to select plant images.'
        );
        return;
      }

      // Pick image
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
        base64: true,
      });

      if (!result.canceled && result.assets[0].base64) {
        const base64Image = `data:image/jpeg;base64,${result.assets[0].base64}`;
        setSelectedImage(base64Image);
        setResult(null);
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to pick image. Please try again.');
    }
  };

  // Take photo with camera
  const takePhoto = async () => {
    try {
      // Request permissions
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      
      if (status !== 'granted') {
        Alert.alert(
          'Permission Required',
          'Please allow camera access to take plant photos.'
        );
        return;
      }

      // Take photo
      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
        base64: true,
      });

      if (!result.canceled && result.assets[0].base64) {
        const base64Image = `data:image/jpeg;base64,${result.assets[0].base64}`;
        setSelectedImage(base64Image);
        setResult(null);
      }
    } catch (error) {
      console.error('Error taking photo:', error);
      Alert.alert('Error', 'Failed to take photo. Please try again.');
    }
  };

  // Analyze plant image
  const analyzeImage = async () => {
    if (!selectedImage) return;

    setAnalyzing(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/analyze-plant`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_base64: selectedImage,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to analyze image');
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error analyzing image:', error);
      Alert.alert('Error', 'Failed to analyze plant. Please try again.');
    } finally {
      setAnalyzing(false);
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('healthy')) return '#4CAF50';
    if (statusLower.includes('minor')) return '#8BC34A';
    if (statusLower.includes('moderate')) return '#FF9800';
    if (statusLower.includes('severe')) return '#F44336';
    if (statusLower.includes('critical')) return '#D32F2F';
    return '#9E9E9E';
  };

  // Reset to initial state
  const reset = () => {
    setSelectedImage(null);
    setResult(null);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Header */}
      <View style={styles.header}>
        <Ionicons name="leaf" size={40} color="#4CAF50" />
        <Text style={styles.title}>Plant Health Scanner</Text>
        <Text style={styles.subtitle}>Analyze your plants with AI</Text>
      </View>

      {/* No image selected - show buttons */}
      {!selectedImage && !result && (
        <View style={styles.buttonContainer}>
          <TouchableOpacity style={styles.actionButton} onPress={takePhoto}>
            <Ionicons name="camera" size={32} color="#fff" />
            <Text style={styles.buttonText}>Take Photo</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionButton} onPress={pickImage}>
            <Ionicons name="images" size={32} color="#fff" />
            <Text style={styles.buttonText}>Choose from Gallery</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Image selected but not analyzed */}
      {selectedImage && !result && (
        <View style={styles.imageSection}>
          <Image source={{ uri: selectedImage }} style={styles.selectedImage} />
          
          <View style={styles.actionRow}>
            <TouchableOpacity style={styles.secondaryButton} onPress={reset}>
              <Ionicons name="close" size={20} color="#666" />
              <Text style={styles.secondaryButtonText}>Cancel</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.analyzeButton, analyzing && styles.disabledButton]}
              onPress={analyzeImage}
              disabled={analyzing}
            >
              {analyzing ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <Ionicons name="search" size={20} color="#fff" />
              )}
              <Text style={styles.analyzeButtonText}>
                {analyzing ? 'Analyzing...' : 'Analyze Plant'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Results */}
      {result && (
        <View style={styles.resultsSection}>
          <Image source={{ uri: result.image_base64 }} style={styles.resultImage} />

          {/* Health Status Badge */}
          <View
            style={[
              styles.statusBadge,
              { backgroundColor: getStatusColor(result.health_status) },
            ]}
          >
            <Text style={styles.statusText}>{result.health_status}</Text>
          </View>

          {/* Issues */}
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="alert-circle" size={24} color="#F44336" />
              <Text style={styles.cardTitle}>Issues Detected</Text>
            </View>
            {result.issues.map((issue, index) => (
              <View key={index} style={styles.listItem}>
                <Text style={styles.bullet}>•</Text>
                <Text style={styles.listText}>{issue}</Text>
              </View>
            ))}
          </View>

          {/* Remedies */}
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="medical" size={24} color="#4CAF50" />
              <Text style={styles.cardTitle}>Recommended Remedies</Text>
            </View>
            {result.remedies.map((remedy, index) => (
              <View key={index} style={styles.listItem}>
                <Text style={styles.bullet}>•</Text>
                <Text style={styles.listText}>{remedy}</Text>
              </View>
            ))}
          </View>

          {/* Detailed Analysis */}
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="document-text" size={24} color="#2196F3" />
              <Text style={styles.cardTitle}>Detailed Analysis</Text>
            </View>
            <Text style={styles.detailedText}>{result.detailed_analysis}</Text>
          </View>

          {/* Scan Another Button */}
          <TouchableOpacity style={styles.scanAnotherButton} onPress={reset}>
            <Ionicons name="camera" size={20} color="#fff" />
            <Text style={styles.scanAnotherText}>Scan Another Plant</Text>
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  contentContainer: {
    padding: 16,
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingBottom: 32,
  },
  header: {
    alignItems: 'center',
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#2E7D32',
    marginTop: 12,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginTop: 4,
  },
  buttonContainer: {
    gap: 16,
  },
  actionButton: {
    backgroundColor: '#4CAF50',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    borderRadius: 12,
    gap: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  imageSection: {
    gap: 16,
  },
  selectedImage: {
    width: '100%',
    height: 300,
    borderRadius: 12,
    backgroundColor: '#e0e0e0',
  },
  actionRow: {
    flexDirection: 'row',
    gap: 12,
  },
  secondaryButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    gap: 8,
  },
  secondaryButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '600',
  },
  analyzeButton: {
    flex: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#2196F3',
    gap: 8,
  },
  disabledButton: {
    opacity: 0.6,
  },
  analyzeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  resultsSection: {
    gap: 16,
  },
  resultImage: {
    width: '100%',
    height: 250,
    borderRadius: 12,
    backgroundColor: '#e0e0e0',
  },
  statusBadge: {
    alignSelf: 'center',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 24,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  statusText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  listItem: {
    flexDirection: 'row',
    marginBottom: 8,
    paddingRight: 8,
  },
  bullet: {
    fontSize: 16,
    color: '#666',
    marginRight: 8,
  },
  listText: {
    flex: 1,
    fontSize: 15,
    color: '#555',
    lineHeight: 22,
  },
  detailedText: {
    fontSize: 15,
    color: '#555',
    lineHeight: 22,
  },
  scanAnotherButton: {
    backgroundColor: '#4CAF50',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    gap: 8,
    marginTop: 8,
  },
  scanAnotherText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
