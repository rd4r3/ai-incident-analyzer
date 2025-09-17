import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform 
} from 'react-native';
import { 
  TextInput, 
  Card, 
  Title, 
  Paragraph, 
  ActivityIndicator,
  SegmentedButtons,
  RadioButton 
} from 'react-native-paper';
import { Ionicons } from '@expo/vector-icons';

import { incidentAPI } from '../services/api';
import { COLORS, ANALYSIS_TYPES } from '../utils/constants';
// import ErrorMessage from '../components/ErrorMessage';
import AnalysisResult from '../components/AnalysisResult';

export default function AnalysisScreen() {
  const [query, setQuery] = useState('');
  const [analysisType, setAnalysisType] = useState(ANALYSIS_TYPES.ROOT_CAUSE);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  const analyzeIncident = async () => {
    if (!query.trim()) {
      setError('Please enter a description or question');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let response;
      
      switch (analysisType) {
        case ANALYSIS_TYPES.ROOT_CAUSE:
          response = await incidentAPI.analyzeRootCause(query);
          break;
        case ANALYSIS_TYPES.PATTERNS:
          response = await incidentAPI.analyzePatterns(query);
          break;
        case ANALYSIS_TYPES.SEARCH:
          response = await incidentAPI.searchIncidents(query);
          break;
        default:
          throw new Error('Invalid analysis type');
      }

      if (response.data) {
        setResult(response.data);
        // Add to history
        setHistory(prev => [
          {
            id: Date.now(),
            query,
            type: analysisType,
            result: response.data,
            timestamp: new Date().toISOString()
          },
          ...prev.slice(0, 9) // Keep only last 10
        ]);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const clearResults = () => {
    setResult(null);
    setError(null);
    setQuery('');
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView>
        <View style={styles.header}>
          <Ionicons name="analytics" size={32} color={COLORS.primary} />
          <Text style={styles.title}>Incident Analysis</Text>
          <Text style={styles.subtitle}>AI-powered root cause analysis</Text>
        </View>

        {/* {error && <ErrorMessage message={error} onRetry={analyzeIncident} />} */}

        {/* Analysis Type Selection */}
        <Card style={styles.card}>
          <Card.Content>
            <Title>Analysis Type</Title>
            <RadioButton.Group onValueChange={setAnalysisType} value={analysisType}>
              <View style={styles.radioOption}>
                <RadioButton value={ANALYSIS_TYPES.ROOT_CAUSE} />
                <Text>Root Cause Analysis</Text>
              </View>
              <View style={styles.radioOption}>
                <RadioButton value={ANALYSIS_TYPES.PATTERNS} />
                <Text>Pattern Analysis</Text>
              </View>
              <View style={styles.radioOption}>
                <RadioButton value={ANALYSIS_TYPES.SEARCH} />
                <Text>Search Incidents</Text>
              </View>
            </RadioButton.Group>
          </Card.Content>
        </Card>

        {/* Query Input */}
        <Card style={styles.card}>
          <Card.Content>
            <Title>Describe the Incident</Title>
            <TextInput
              mode="outlined"
              multiline
              numberOfLines={4}
              placeholder="Example: Database connection issues during peak hours causing timeouts..."
              value={query}
              onChangeText={setQuery}
              style={styles.textInput}
            />
          </Card.Content>
        </Card>

        {/* Action Buttons */}
        <View style={styles.buttonRow}>
          <TouchableOpacity
            style={[styles.button, styles.primaryButton]}
            onPress={analyzeIncident}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color={COLORS.white} />
            ) : (
              <>
                <Ionicons name="rocket" size={20} color={COLORS.white} />
                <Text style={styles.buttonText}>Analyze</Text>
              </>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.secondaryButton]}
            onPress={clearResults}
          >
            <Ionicons name="trash" size={20} color={COLORS.dark} />
            <Text style={styles.buttonText}>Clear</Text>
          </TouchableOpacity>
        </View>

        {/* Results */}
        {result && (
          <AnalysisResult 
            result={result} 
            analysisType={analysisType}
            query={query}
          />
        )}

        {/* Analysis History */}
        {history.length > 0 && (
          <Card style={styles.card}>
            <Card.Content>
              <Title>Recent Analyses</Title>
              {history.map((item) => (
                <TouchableOpacity
                  key={item.id}
                  style={styles.historyItem}
                  onPress={() => {
                    setQuery(item.query);
                    setAnalysisType(item.type);
                    setResult(item.result);
                  }}
                >
                  <Text style={styles.historyQuery} numberOfLines={1}>
                    {item.query}
                  </Text>
                  <Text style={styles.historyType}>
                    {item.type.replace('_', ' ').toUpperCase()}
                  </Text>
                </TouchableOpacity>
              ))}
            </Card.Content>
          </Card>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.primary,
    marginTop: 8,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.dark,
  },
  card: {
    marginBottom: 16,
  },
  textInput: {
    marginTop: 8,
  },
  radioOption: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 4,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  button: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 8,
    marginHorizontal: 4,
  },
  primaryButton: {
    backgroundColor: COLORS.primary,
  },
  secondaryButton: {
    backgroundColor: COLORS.light,
    borderWidth: 1,
    borderColor: COLORS.dark,
  },
  buttonText: {
    color: COLORS.white,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  historyItem: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  historyQuery: {
    fontSize: 14,
    fontWeight: '500',
  },
  historyType: {
    fontSize: 12,
    color: COLORS.dark,
    marginTop: 4,
  },
});