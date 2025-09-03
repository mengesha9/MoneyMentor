// Diagnostic Test Debugger - Comprehensive monitoring of the completion flow
export class DiagnosticDebugger {
  private static instance: DiagnosticDebugger;
  private logs: Array<{timestamp: string, component: string, action: string, data: any}> = [];
  private isEnabled = true;

  static getInstance(): DiagnosticDebugger {
    if (!DiagnosticDebugger.instance) {
      DiagnosticDebugger.instance = new DiagnosticDebugger();
    }
    return DiagnosticDebugger.instance;
  }

  log(component: string, action: string, data: any) {
    if (!this.isEnabled) return;
    
    const logEntry = {
      timestamp: new Date().toISOString(),
      component,
      action,
      data
    };
    
    this.logs.push(logEntry);
    
    // Console output with emojis for easy identification
    console.log(`🔍 [${component}] ${action}:`, data);
    
    // Also log to localStorage for persistence across page reloads
    try {
      const existingLogs = localStorage.getItem('diagnostic_debug_logs') || '[]';
      const allLogs = JSON.parse(existingLogs);
      allLogs.push(logEntry);
      localStorage.setItem('diagnostic_debug_logs', JSON.stringify(allLogs.slice(-100))); // Keep last 100 logs
    } catch (e) {
      console.warn('Failed to save debug log to localStorage:', e);
    }
  }

  // Monitor diagnostic state changes
  monitorDiagnosticState(state: any, source: string) {
    this.log('DiagnosticState', `State Change from ${source}`, {
      currentQuestionIndex: state.currentQuestionIndex,
      totalQuestions: state.test?.questions?.length || 0,
      isActive: state.isActive,
      hasQuizId: !!state.quizId,
      hasBackendResult: !!state.backendResult,
      answersCount: state.answers?.length || 0,
      timestamp: Date.now()
    });
  }

  // Monitor API calls
  monitorApiCall(endpoint: string, requestData: any, responseData: any) {
    this.log('API', `${endpoint} Call`, {
      request: requestData,
      response: responseData,
      timestamp: Date.now()
    });
  }

  // Monitor component rendering
  monitorRendering(component: string, props: any, state: any) {
    this.log('Rendering', `${component} Render`, {
      props: props,
      state: state,
      timestamp: Date.now()
    });
  }

  // Monitor event handlers
  monitorEventHandler(component: string, handler: string, eventData: any) {
    this.log('EventHandler', `${component} ${handler}`, {
      eventData,
      timestamp: Date.now()
    });
  }

  // Monitor navigation changes
  monitorNavigation(from: string, to: string, trigger: string) {
    this.log('Navigation', `Route Change`, {
      from,
      to,
      trigger,
      timestamp: Date.now()
    });
  }

  // Get all logs
  getLogs() {
    return [...this.logs];
  }

  // Get logs from localStorage
  getPersistedLogs() {
    try {
      const logs = localStorage.getItem('diagnostic_debug_logs');
      return logs ? JSON.parse(logs) : [];
    } catch (e) {
      console.warn('Failed to retrieve persisted logs:', e);
      return [];
    }
  }

  // Clear logs
  clearLogs() {
    this.logs = [];
    localStorage.removeItem('diagnostic_debug_logs');
  }

  // Export logs as JSON
  exportLogs() {
    const allLogs = [...this.logs, ...this.getPersistedLogs()];
    const blob = new Blob([JSON.stringify(allLogs, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `diagnostic-debug-logs-${new Date().toISOString()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Analyze logs for patterns
  analyzeLogs() {
    const allLogs = [...this.logs, ...this.getPersistedLogs()];
    
    const analysis = {
      totalLogs: allLogs.length,
      components: {} as Record<string, number>,
      actions: {} as Record<string, number>,
      apiCalls: [] as any[],
      stateChanges: [] as any[],
      navigationChanges: [] as any[],
      potentialIssues: [] as string[]
    };

    allLogs.forEach(log => {
      // Count components and actions
      analysis.components[log.component] = (analysis.components[log.component] || 0) + 1;
      analysis.actions[log.action] = (analysis.actions[log.action] || 0) + 1;

      // Categorize logs
      if (log.component === 'API') {
        analysis.apiCalls.push(log);
      } else if (log.action.includes('State Change')) {
        analysis.stateChanges.push(log);
      } else if (log.action.includes('Route Change')) {
        analysis.navigationChanges.push(log);
      }
    });

    // Detect potential issues
    if (analysis.apiCalls.length > 10) {
      analysis.potentialIssues.push('High number of API calls detected - possible infinite loop');
    }

    const duplicateApiCalls = analysis.apiCalls.filter((call, index, arr) => 
      arr.findIndex(c => c.data.request === call.data.request) !== index
    );
    
    if (duplicateApiCalls.length > 0) {
      analysis.potentialIssues.push(`Duplicate API calls detected: ${duplicateApiCalls.length} duplicates`);
    }

    return analysis;
  }

  // Enable/disable logging
  setEnabled(enabled: boolean) {
    this.isEnabled = enabled;
    this.log('Debugger', 'Logging Status Changed', { enabled });
  }

  // Create a summary report
  generateReport() {
    const analysis = this.analyzeLogs();
    const report = {
      summary: `Diagnostic Debug Report - ${new Date().toLocaleString()}`,
      totalLogs: analysis.totalLogs,
      components: analysis.components,
      actions: analysis.actions,
      apiCalls: analysis.apiCalls.length,
      stateChanges: analysis.stateChanges.length,
      navigationChanges: analysis.navigationChanges.length,
      potentialIssues: analysis.potentialIssues,
      recommendations: [] as string[]
    };

    // Generate recommendations based on analysis
    if (analysis.potentialIssues.length > 0) {
      report.recommendations.push('Review and fix identified issues above');
    }

    if (analysis.apiCalls.length > 5) {
      report.recommendations.push('Consider implementing API call debouncing or caching');
    }

    if (analysis.stateChanges.length > 10) {
      report.recommendations.push('Review state management to reduce unnecessary updates');
    }

    return report;
  }
}

// Export singleton instance
export const diagnosticDebugger = DiagnosticDebugger.getInstance();

// Helper functions for easy monitoring
export const debugDiagnosticState = (state: any, source: string) => 
  diagnosticDebugger.monitorDiagnosticState(state, source);

export const debugApiCall = (endpoint: string, requestData: any, responseData: any) => 
  diagnosticDebugger.monitorApiCall(endpoint, requestData, responseData);

export const debugRendering = (component: string, props: any, state: any) => 
  diagnosticDebugger.monitorRendering(component, props, state);

export const debugEventHandler = (component: string, handler: string, eventData: any) => 
  diagnosticDebugger.monitorEventHandler(component, handler, eventData);

export const debugNavigation = (from: string, to: string, trigger: string) => 
  diagnosticDebugger.monitorNavigation(from, to, trigger);

// Global access for console debugging
declare global {
  interface Window {
    diagnosticDebugger: typeof diagnosticDebugger;
    debugDiagnostic: {
      state: typeof debugDiagnosticState;
      api: typeof debugApiCall;
      render: typeof debugRendering;
      event: typeof debugEventHandler;
      nav: typeof debugNavigation;
      logs: () => any[];
      analysis: () => any;
      report: () => any;
      export: () => void;
      clear: () => void;
    };
  }
}

// Attach to window for console access
if (typeof window !== 'undefined') {
  window.diagnosticDebugger = diagnosticDebugger;
  window.debugDiagnostic = {
    state: debugDiagnosticState,
    api: debugApiCall,
    render: debugRendering,
    event: debugEventHandler,
    nav: debugNavigation,
    logs: () => diagnosticDebugger.getLogs(),
    analysis: () => diagnosticDebugger.analyzeLogs(),
    report: () => diagnosticDebugger.generateReport(),
    export: () => diagnosticDebugger.exportLogs(),
    clear: () => diagnosticDebugger.clearLogs()
  };
  
  console.log('🔍 Diagnostic Debugger loaded! Use window.debugDiagnostic.* for debugging');
  console.log('📊 Available commands:');
  console.log('  debugDiagnostic.logs() - Get current logs');
  console.log('  debugDiagnostic.analysis() - Analyze logs for patterns');
  console.log('  debugDiagnostic.report() - Generate summary report');
  console.log('  debugDiagnostic.export() - Export logs as JSON');
  console.log('  debugDiagnostic.clear() - Clear all logs');
} 