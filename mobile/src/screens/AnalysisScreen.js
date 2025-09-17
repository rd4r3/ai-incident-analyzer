import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import {
  TextInput,
  Card,
  Title,
  ActivityIndicator,
  RadioButton,
} from 'react-native-paper';
import { Ionicons } from '@expo/vector-icons';

import { incidentAPI } from '../services/api';
import { COLORS, ANALYSIS_TYPES } from '../utils/constants';
// import ErrorMessage from '../components/ErrorMessage';
import AnalysisResult from '../components/AnalysisResult';

const AnalysisTypeSelector = ({ value, onChange }) => (
  <Card style={styles.card}>
    <Card.Content>
      <Title style={styles.basicText}>Analysis Type</Title>
      <RadioButton.Group onValueChange={onChange} value={value}>
        {Object.entries(ANALYSIS_TYPES).map(([key, val]) => (
          <View key={val} style={styles.radioOption}>
            <RadioButton value={val} />
            <Text style={styles.basicText}>{val.replace('_', ' ').toUpperCase()}</Text>
          </View>
        ))}
      </RadioButton.Group>
    </Card.Content>
  </Card>
);

const ActionButtons = ({ onAnalyze, onClear, loading }) => (
  <View style={styles.buttonRow}>
    <TouchableOpacity
      style={[styles.button, styles.primaryButton]}
      onPress={onAnalyze}
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
      onPress={onClear}
    >
      <Ionicons name="trash" size={20} color={COLORS.dark} />
      <Text style={styles.buttonText}>Clear</Text>
    </TouchableOpacity>
  </View>
);

const HistoryList = ({ items, onSelect }) => (
  <Card style={styles.card}>
    <Card.Content>
      <Title>Recent Analyses</Title>
      {items.map((item) => (
        <TouchableOpacity
          key={item.id}
          style={styles.historyItem}
          onPress={() => onSelect(item)}
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
);

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
      const response = await {
        [ANALYSIS_TYPES.ROOT_CAUSE]: incidentAPI.analyzeRootCause,
        [ANALYSIS_TYPES.PATTERNS]: incidentAPI.analyzePatterns,
        [ANALYSIS_TYPES.SEARCH]: incidentAPI.searchIncidents,
      }[analysisType](query);

      if (response.data) {
        setResult(response.data);
        setHistory((prev) => [
          {
            id: Date.now(),
            query,
            type: analysisType,
            result: response.data,
            timestamp: new Date().toISOString(),
          },
          ...prev.slice(0, 9),
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
    setQuery('');
    setResult(null);
    setError(null);
  };

  const handleHistorySelect = (item) => {
    setQuery(item.query);
    setAnalysisType(item.type);
    setResult(item.result);
  };

  return (
      <ScrollView
            style={styles.container}
          >
        <View style={styles.header}>
          {/* <Ionicons name="analytics" size={32} color={COLORS.primary} /> */}
          <Text style={styles.title}>Incident Analysis</Text>
          <Text style={styles.subtitle}>AI-powered root cause analysis</Text>
        </View>

        {/* {error && <ErrorMessage message={error} onRetry={analyzeIncident} />} */}

        <AnalysisTypeSelector value={analysisType} onChange={setAnalysisType} />

        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.basicText}>Describe the Incident</Title>
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

        <ActionButtons onAnalyze={analyzeIncident} onClear={clearResults} loading={loading} />

        {result && (
          <AnalysisResult result={result} analysisType={analysisType} query={query} />
        )}

        {history.length > 0 && <HistoryList items={history} onSelect={handleHistorySelect} />}
      </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    padding: 16,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    color: COLORS.text,
    fontSize: 16,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: COLORS.primary,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.text,
  },
  card: {
    marginBottom: 16,
    backgroundColor: COLORS.background,
    color: COLORS.text ,
    padding: 16,
    borderRadius: 12,
  },
  textInput: {
    marginTop: 8,
    backgroundColor: COLORS.background,
    color: COLORS.text
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
   basicText: {
    color: COLORS.text,
  },
});
