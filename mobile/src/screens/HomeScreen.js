import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { Card, Title, Paragraph, ActivityIndicator } from 'react-native-paper';
import { Ionicons } from '@expo/vector-icons';

import { incidentAPI } from '../services/api';
import { COLORS } from '../utils/constants';
// import ErrorMessage from '../components/ErrorMessage';

const StatCard = ({ icon, color, value, label }) => (
  <Card style={styles.statCard}>
    <Card.Content style={styles.cardContent}>
      <Ionicons name={icon} size={32} color={color} />
      <Title style={styles.statNumber}>{value}</Title>
      <Paragraph style={styles.basicText}>{label}</Paragraph>
    </Card.Content>
  </Card>
);

const ActionButton = ({ icon, label, onPress }) => (
  <TouchableOpacity style={styles.actionButton} onPress={onPress}>
    <Ionicons name={icon} size={24} color={COLORS.white} />
    <Text style={styles.actionText}>{label}</Text>
  </TouchableOpacity>
);

export default function HomeScreen({ navigation }) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    totalIncidents: 0,
    criticalIncidents: 0,
    averageMTTR: 0,
    categories: {},
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setError(null);
      const [healthResponse, incidentsResponse] = await Promise.all([
        incidentAPI.healthCheck(),
        incidentAPI.getIncidents(),
      ]);

      if (healthResponse.status === 200 && incidentsResponse.data) {
        const incidents = incidentsResponse.data.results || [];
        updateStats(incidents);
      }
    } catch (err) {
      setError('Failed to load data. Please check your connection.');
      console.error('Home screen error:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const updateStats = (incidents) => {
    const total = incidents.length;
    const critical = incidents.filter((i) => i.severity === 'Critical').length;
    const mttrSum = incidents.reduce((sum, i) => sum + (i.resolution_time_hours || 0), 0);
    const averageMTTR = total ? mttrSum / total : 0;

    const categories = incidents.reduce((acc, i) => {
      acc[i.category] = (acc[i.category] || 0) + 1;
      return acc;
    }, {});

    setStats({ totalIncidents: total, criticalIncidents: critical, averageMTTR, categories });
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

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
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* {error && <ErrorMessage message={error} onRetry={loadData} />} */}

      <View style={styles.header}>
        <Text style={styles.title}>AI Incident Analyzer</Text>
        <Text style={styles.subtitle}>Mobile Dashboard</Text>
      </View>

      <View style={styles.actionsRow}>
        <ActionButton icon="analytics" label="Analyze" onPress={() => navigation.navigate('Analysis')} />
        <ActionButton icon="list" label="History" onPress={() => navigation.navigate('History')} />
      </View>

      <View style={styles.statsRow}>
        <StatCard icon="alert-circle" color={COLORS.primary} value={stats.totalIncidents} label="Total Incidents" />
        <StatCard icon="warning" color={COLORS.danger} value={stats.criticalIncidents} label="Critical" />
      </View>

      <View style={styles.statsRow}>
        <StatCard icon="time" color={COLORS.info} value={`${stats.averageMTTR.toFixed(1)}h`} label="Avg MTTR" />
        <StatCard icon="layers" color={COLORS.success} value={Object.keys(stats.categories).length} label="Categories" />
      </View>

      <Card style={styles.sectionCard}>
        <Card.Content>
          <Title style={styles.basicText}>Recent Activity</Title>
          <Paragraph style={styles.basicText}>
            {stats.totalIncidents > 0
              ? `Last updated: ${new Date().toLocaleTimeString()}`
              : 'No incidents recorded yet'}
          </Paragraph>
        </Card.Content>
      </Card>

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
  actionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 24,
  },
  actionButton: {
    backgroundColor: COLORS.primary,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 16,
    alignItems: 'center',
    minWidth: 120,
    shadowColor: '#ccc',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
  },
  actionText: {
    color: COLORS.white,
    fontWeight: '600',
    marginTop: 8,
    fontSize: 14,
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
    backgroundColor: COLORS.accent,
    padding: 12,
    borderRadius: 12,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    color: COLORS.text,
  },
  sectionCard: {
    marginBottom: 16,
    backgroundColor: COLORS.background,
    color: COLORS.text ,
    padding: 16,
    borderRadius: 12,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusText: {
    marginLeft: 8,
    fontSize: 16,
    color: COLORS.text,
  },
  basicText: {
    color: COLORS.text,
  },
});