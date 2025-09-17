import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  TouchableOpacity,
  RefreshControl 
} from 'react-native';
import { Card, Title, Paragraph, ActivityIndicator } from 'react-native-paper';
import { Ionicons } from '@expo/vector-icons';

import { incidentAPI } from '../services/api';
import { COLORS } from '../utils/constants';
// import ErrorMessage from '../components/ErrorMessage';

export default function HomeScreen({ navigation }) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    totalIncidents: 0,
    criticalIncidents: 0,
    averageMTTR: 0,
    categories: {}
  });

  const loadData = async () => {
    try {
      setError(null);
      const [healthResponse, incidentsResponse] = await Promise.all([
        incidentAPI.healthCheck(),
        incidentAPI.getIncidents()
      ]);

      if (healthResponse.status === 200 && incidentsResponse.data) {
        const incidents = incidentsResponse.data.results || [];
        calculateStats(incidents);
      }
    } catch (err) {
      setError('Failed to load data. Please check your connection.');
      console.error('Home screen error:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const calculateStats = (incidents) => {
    const total = incidents.length;
    const critical = incidents.filter(inc => inc.severity === 'Critical').length;
    
    const mttrSum = incidents.reduce((sum, inc) => sum + (inc.resolution_time_hours || 0), 0);
    const averageMTTR = total > 0 ? mttrSum / total : 0;

    const categories = {};
    incidents.forEach(inc => {
      categories[inc.category] = (categories[inc.category] || 0) + 1;
    });

    setStats({
      totalIncidents: total,
      criticalIncidents: critical,
      averageMTTR: averageMTTR,
      categories: categories
    });
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Loading dashboard...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* {error && <ErrorMessage message={error} onRetry={loadData} />} */}

      <View style={styles.header}>
        <Text style={styles.title}>ING Incident Analyzer</Text>
        <Text style={styles.subtitle}>Mobile Dashboard</Text>
      </View>

      {/* Quick Actions */}
      <View style={styles.actionsRow}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => navigation.navigate('Analysis')}
        >
          <Ionicons name="analytics" size={24} color={COLORS.white} />
          <Text style={styles.actionText}>Analyze</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => navigation.navigate('History')}
        >
          <Ionicons name="list" size={24} color={COLORS.white} />
          <Text style={styles.actionText}>History</Text>
        </TouchableOpacity>
      </View>

      {/* Statistics Cards */}
      <View style={styles.statsRow}>
        <Card style={styles.statCard}>
          <Card.Content>
            <Ionicons name="alert-circle" size={32} color={COLORS.primary} />
            <Title style={styles.statNumber}>{stats.totalIncidents}</Title>
            <Paragraph>Total Incidents</Paragraph>
          </Card.Content>
        </Card>

        <Card style={styles.statCard}>
          <Card.Content>
            <Ionicons name="warning" size={32} color={COLORS.danger} />
            <Title style={styles.statNumber}>{stats.criticalIncidents}</Title>
            <Paragraph>Critical</Paragraph>
          </Card.Content>
        </Card>
      </View>

      <View style={styles.statsRow}>
        <Card style={styles.statCard}>
          <Card.Content>
            <Ionicons name="time" size={32} color={COLORS.info} />
            <Title style={styles.statNumber}>{stats.averageMTTR.toFixed(1)}h</Title>
            <Paragraph>Avg MTTR</Paragraph>
          </Card.Content>
        </Card>

        <Card style={styles.statCard}>
          <Card.Content>
            <Ionicons name="layers" size={32} color={COLORS.success} />
            <Title style={styles.statNumber}>{Object.keys(stats.categories).length}</Title>
            <Paragraph>Categories</Paragraph>
          </Card.Content>
        </Card>
      </View>

      {/* Recent Activity */}
      <Card style={styles.sectionCard}>
        <Card.Content>
          <Title>Recent Activity</Title>
          <Paragraph>
            {stats.totalIncidents > 0 
              ? `Last updated: ${new Date().toLocaleTimeString()}`
              : 'No incidents recorded yet'
            }
          </Paragraph>
        </Card.Content>
      </Card>

      {/* API Status */}
      <Card style={styles.sectionCard}>
        <Card.Content>
          <View style={styles.statusRow}>
            <Ionicons 
              name="radio-button-on" 
              size={16} 
              color={error ? COLORS.danger : COLORS.success} 
            />
            <Text style={styles.statusText}>
              API Status: {error ? 'Disconnected' : 'Connected'}
            </Text>
          </View>
        </Card.Content>
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    color: COLORS.dark,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.dark,
  },
  actionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 24,
  },
  actionButton: {
    backgroundColor: COLORS.primary,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    minWidth: 120,
  },
  actionText: {
    color: COLORS.white,
    fontWeight: 'bold',
    marginTop: 8,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  statCard: {
    flex: 1,
    margin: 4,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  sectionCard: {
    marginBottom: 16,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusText: {
    marginLeft: 8,
    fontSize: 16,
  },
});