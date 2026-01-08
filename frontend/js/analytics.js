class RecommendationAnalytics {
  constructor() {
    this.STORAGE_KEY = 'beer_recommendation_analytics';
    this.currentSessionId = this.generateSessionId();
    this.currentRecommendationId = null;
  }

  generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  generateRecommendationId() {
    return 'rec_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  getAnalyticsData() {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('读取分析数据失败:', error);
      return [];
    }
  }

  saveAnalyticsData(data) {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
    } catch (error) {
      console.error('保存分析数据失败:', error);
    }
  }

  recordRecommendationRequest(scenario, familiarity, userInput, inferredParams) {
    this.currentRecommendationId = this.generateRecommendationId();
    
    const record = {
      sessionId: this.currentSessionId,
      recommendationId: this.currentRecommendationId,
      timestamp: new Date().toISOString(),
      type: 'request',
      data: {
        scenario: scenario || null,
        familiarity: familiarity || null,
        userInput: userInput || {},
        inferredParams: inferredParams || {}
      }
    };

    const analyticsData = this.getAnalyticsData();
    analyticsData.push(record);
    this.saveAnalyticsData(analyticsData);

    console.log('记录推荐请求:', record);
    return this.currentRecommendationId;
  }

  recordRecommendationResult(recommendations) {
    if (!this.currentRecommendationId) {
      console.warn('没有有效的推荐ID，无法记录结果');
      return;
    }

    const record = {
      sessionId: this.currentSessionId,
      recommendationId: this.currentRecommendationId,
      timestamp: new Date().toISOString(),
      type: 'result',
      data: {
        recommendations: recommendations || []
      }
    };

    const analyticsData = this.getAnalyticsData();
    analyticsData.push(record);
    this.saveAnalyticsData(analyticsData);

    console.log('记录推荐结果:', record);
  }

  recordUserAction(actionType, beerName, additionalData = {}) {
    if (!this.currentRecommendationId) {
      console.warn('没有有效的推荐ID，无法记录用户操作');
      return;
    }

    const record = {
      sessionId: this.currentSessionId,
      recommendationId: this.currentRecommendationId,
      timestamp: new Date().toISOString(),
      type: 'action',
      data: {
        actionType: actionType,
        beerName: beerName || null,
        ...additionalData
      }
    };

    const analyticsData = this.getAnalyticsData();
    analyticsData.push(record);
    this.saveAnalyticsData(analyticsData);

    console.log('记录用户操作:', record);
  }

  getRecommendationHistory(limit = 50) {
    const analyticsData = this.getAnalyticsData();
    return analyticsData.slice(-limit);
  }

  getRecommendationById(recommendationId) {
    const analyticsData = this.getAnalyticsData();
    return analyticsData.filter(record => record.recommendationId === recommendationId);
  }

  getSessionHistory(sessionId) {
    const analyticsData = this.getAnalyticsData();
    return analyticsData.filter(record => record.sessionId === sessionId);
  }

  getStatistics() {
    const analyticsData = this.getAnalyticsData();
    
    const stats = {
      totalRequests: 0,
      totalResults: 0,
      totalActions: 0,
      actionBreakdown: {
        buy: 0,
        favorite: 0,
        view: 0
      },
      scenarioBreakdown: {},
      familiarityBreakdown: {
        beginner: 0,
        advanced: 0
      },
      topBeers: {},
      topBreweries: {}
    };

    analyticsData.forEach(record => {
      if (record.type === 'request') {
        stats.totalRequests++;
        
        if (record.data.scenario) {
          stats.scenarioBreakdown[record.data.scenario] = 
            (stats.scenarioBreakdown[record.data.scenario] || 0) + 1;
        }
        
        if (record.data.familiarity) {
          const familiarity = record.data.familiarity.toLowerCase();
          if (familiarity === 'beginner') {
            stats.familiarityBreakdown.beginner++;
          } else if (familiarity === 'advanced') {
            stats.familiarityBreakdown.advanced++;
          }
        }
      } else if (record.type === 'result') {
        stats.totalResults++;
        
        if (record.data.recommendations && Array.isArray(record.data.recommendations)) {
          record.data.recommendations.forEach(beer => {
            if (beer.name) {
              stats.topBeers[beer.name] = (stats.topBeers[beer.name] || 0) + 1;
            }
            if (beer.brewery) {
              stats.topBreweries[beer.brewery] = (stats.topBreweries[beer.brewery] || 0) + 1;
            }
          });
        }
      } else if (record.type === 'action') {
        stats.totalActions++;
        
        if (record.data.actionType) {
          const actionType = record.data.actionType.toLowerCase();
          if (actionType === 'buy') {
            stats.actionBreakdown.buy++;
          } else if (actionType === 'favorite') {
            stats.actionBreakdown.favorite++;
          } else if (actionType === 'view') {
            stats.actionBreakdown.view++;
          }
        }
      }
    });

    return stats;
  }

  exportAnalyticsData() {
    const analyticsData = this.getAnalyticsData();
    const dataStr = JSON.stringify(analyticsData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `beer_analytics_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
  }

  clearAnalyticsData() {
    localStorage.removeItem(this.STORAGE_KEY);
    this.currentSessionId = this.generateSessionId();
    this.currentRecommendationId = null;
    console.log('分析数据已清除');
  }

  getRecommendationSummary(recommendationId) {
    const records = this.getRecommendationById(recommendationId);
    
    if (records.length === 0) {
      return null;
    }

    const summary = {
      recommendationId: recommendationId,
      sessionId: records[0].sessionId,
      timestamp: records[0].timestamp,
      scenario: null,
      familiarity: null,
      userInput: null,
      inferredParams: null,
      recommendations: null,
      actions: []
    };

    records.forEach(record => {
      if (record.type === 'request') {
        summary.scenario = record.data.scenario;
        summary.familiarity = record.data.familiarity;
        summary.userInput = record.data.userInput;
        summary.inferredParams = record.data.inferredParams;
      } else if (record.type === 'result') {
        summary.recommendations = record.data.recommendations;
      } else if (record.type === 'action') {
        summary.actions.push({
          timestamp: record.timestamp,
          actionType: record.data.actionType,
          beerName: record.data.beerName
        });
      }
    });

    return summary;
  }
}

const analytics = new RecommendationAnalytics();
