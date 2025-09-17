import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Card, Title } from 'react-native-paper';
import Markdown from 'react-native-markdown-display';
import { COLORS, ANALYSIS_TYPES } from '../utils/constants';

export default function AnalysisResult({ result, analysisType, query }) {
  const renderContent = () => {
    if (!result) return null;

    switch (analysisType) {
      case ANALYSIS_TYPES.ROOT_CAUSE:
      case ANALYSIS_TYPES.PATTERNS:
        return (
          <ScrollView>
            <Markdown style={markdownStyles}>
              {result.result || 'No analysis result available'}
            </Markdown>
          </ScrollView>
        );

      case ANALYSIS_TYPES.SEARCH:
        return (
          <View>
            <Text style={styles.resultCount}>
              Found {result.results?.length || 0} similar incidents
            </Text>
            {result.results?.map((item, index) => (
              <Card key={index} style={styles.searchResultCard}>
                <Card.Content>
                  <Text style={styles.incidentId}>
                    {item.metadata?.incident_id || 'Unknown ID'}
                  </Text>
                  <Text style={styles.category}>
                    Category: {item.metadata?.category || 'Unknown'}
                  </Text>
                  <Text style={styles.severity}>
                    Severity: {item.metadata?.severity || 'Unknown'}
                  </Text>
                  <Text style={styles.content} numberOfLines={3}>
                    {item.content}
                  </Text>
                  {item.similarity_score && (
                    <Text style={styles.similarity}>
                      Similarity: {(item.similarity_score * 100).toFixed(1)}%
                    </Text>
                  )}
                </Card.Content>
              </Card>
            ))}
          </View>
        );

      default:
        return <Text>Unknown analysis type</Text>;
    }
  };

  return (
    <Card style={styles.container}>
      <Card.Content>
        <Title>Analysis Results</Title>
        <Text style={styles.query}>Query: {query}</Text>
        {renderContent()}
      </Card.Content>
    </Card>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  query: {
    fontSize: 14,
    color: COLORS.dark,
    marginBottom: 12,
    fontStyle: 'italic',
  },
  resultCount: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  searchResultCard: {
    marginBottom: 8,
  },
  incidentId: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  category: {
    fontSize: 14,
    color: COLORS.dark,
  },
  severity: {
    fontSize: 14,
    color: COLORS.danger,
  },
  content: {
    fontSize: 14,
    marginTop: 8,
  },
  similarity: {
    fontSize: 12,
    color: COLORS.info,
    marginTop: 4,
  },
});

const markdownStyles = {
  body: {
    fontSize: 16,
    lineHeight: 24,
  },
  heading1: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.primary,
    marginVertical: 8,
  },
  heading2: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.dark,
    marginVertical: 6,
  },
  strong: {
    fontWeight: 'bold',
  },
  em: {
    fontStyle: 'italic',
  },
};