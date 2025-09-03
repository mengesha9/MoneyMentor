import React, { useState, useEffect } from 'react';
import { Button, Card, CardContent, Typography, Box, Chip, Alert } from '@mui/material';
import { Sync, Settings, CheckCircle, Error, Schedule } from '@mui/icons-material';

interface SyncStatus {
  triggered_sync: {
    pending_sync: boolean;
    last_sync_time: string | null;
    sync_cooldown_seconds: number;
    time_since_last_sync: number | null;
  };
  manual_sync: {
    sync_in_progress: boolean;
    last_sync_time: string | null;
    stats: {
      total_syncs: number;
      successful_syncs: number;
      failed_syncs: number;
      last_sync_duration: number;
    };
  };
  config: {
    intervals: Record<string, number>;
    settings: Record<string, boolean>;
  };
}

const SyncManager: React.FC = () => {
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const fetchSyncStatus = async () => {
    try {
      const response = await fetch('/api/admin/sync/stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch sync status');
      }
      
      const data = await response.json();
      setSyncStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sync status');
    }
  };

  const triggerManualSync = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch('/api/admin/sync/trigger?force=true', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to trigger sync');
      }
      
      const data = await response.json();
      setSuccess(data.message || 'Sync triggered successfully');
      await fetchSyncStatus(); // Refresh status
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to trigger sync');
    } finally {
      setLoading(false);
    }
  };

  const updateSyncInterval = async (intervalType: string, seconds: number) => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await fetch(`/api/admin/sync/config/interval/${intervalType}?seconds=${seconds}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to update sync interval');
      }
      
      const data = await response.json();
      setSuccess(data.message || 'Sync interval updated successfully');
      await fetchSyncStatus(); // Refresh status
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update sync interval');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSyncStatus();
  }, []);

  if (!syncStatus) {
    return <div>Loading sync status...</div>;
  }

  const formatTime = (seconds: number | null) => {
    if (!seconds) return 'Never';
    if (seconds < 60) return `${Math.round(seconds)}s ago`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
    return `${Math.round(seconds / 3600)}h ago`;
  };

  return (
    <Box sx={{ p: 3, maxWidth: 800, margin: '0 auto' }}>
      <Typography variant="h4" gutterBottom>
        <Settings sx={{ mr: 1, verticalAlign: 'middle' }} />
        Sync Manager
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Button
          variant="contained"
          startIcon={<Sync />}
          onClick={triggerManualSync}
          disabled={loading}
        >
          {loading ? 'Syncing...' : 'Trigger Manual Sync'}
        </Button>
        
        <Button
          variant="outlined"
          onClick={fetchSyncStatus}
          disabled={loading}
        >
          Refresh Status
        </Button>
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
        {/* Triggered Sync Status */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <Schedule sx={{ mr: 1, verticalAlign: 'middle' }} />
              Triggered Sync
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Chip
                label={syncStatus.triggered_sync.pending_sync ? 'Pending' : 'Idle'}
                color={syncStatus.triggered_sync.pending_sync ? 'warning' : 'default'}
                size="small"
              />
            </Box>
            
            <Typography variant="body2" color="text.secondary">
              Last sync: {formatTime(syncStatus.triggered_sync.time_since_last_sync)}
            </Typography>
            
            <Typography variant="body2" color="text.secondary">
              Cooldown: {syncStatus.triggered_sync.sync_cooldown_seconds}s
            </Typography>
          </CardContent>
        </Card>

        {/* Manual Sync Status */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <Sync sx={{ mr: 1, verticalAlign: 'middle' }} />
              Manual Sync
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Chip
                label={syncStatus.manual_sync.sync_in_progress ? 'In Progress' : 'Available'}
                color={syncStatus.manual_sync.sync_in_progress ? 'warning' : 'success'}
                size="small"
              />
            </Box>
            
            <Typography variant="body2" color="text.secondary">
              Total syncs: {syncStatus.manual_sync.stats.total_syncs}
            </Typography>
            
            <Typography variant="body2" color="text.secondary">
              Success rate: {syncStatus.manual_sync.stats.total_syncs > 0 
                ? Math.round((syncStatus.manual_sync.stats.successful_syncs / syncStatus.manual_sync.stats.total_syncs) * 100)
                : 0}%
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Sync Configuration */}
      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Sync Configuration
          </Typography>
          
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Sync Intervals
              </Typography>
              {Object.entries(syncStatus.config.intervals).map(([key, value]) => (
                <Box key={key} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="body2" sx={{ minWidth: 200 }}>
                    {key.replace(/_/g, ' ')}:
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {value}s
                  </Typography>
                  <Button
                    size="small"
                    onClick={() => {
                      const newValue = prompt(`Enter new value for ${key} (seconds):`, value.toString());
                      if (newValue && !isNaN(Number(newValue))) {
                        updateSyncInterval(key, Number(newValue));
                      }
                    }}
                  >
                    Change
                  </Button>
                </Box>
              ))}
            </Box>
            
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Sync Settings
              </Typography>
              {Object.entries(syncStatus.config.settings).map(([key, value]) => (
                <Box key={key} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="body2" sx={{ minWidth: 200 }}>
                    {key.replace(/_/g, ' ')}:
                  </Typography>
                  <Chip
                    label={value ? 'Enabled' : 'Disabled'}
                    color={value ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
              ))}
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SyncManager;