// src/services/decisionEngine.js
class DecisionEngine {
  constructor() {
    this.sensorStandards = {
      nitrogen: { min: 40, max: 80, optimal: 60, unit: 'ppm', description: 'Leaf growth and color' },
      phosphorus: { min: 20, max: 50, optimal: 35, unit: 'ppm', description: 'Root and flower development' },
      potassium: { min: 30, max: 70, optimal: 50, unit: 'ppm', description: 'Disease resistance' },
      moisture: { min: 20, max: 40, optimal: 30, unit: '%', description: 'Soil water content' },
      temperature: { min: 15, max: 30, optimal: 22, unit: '°C', description: 'Ambient temperature' },
      ph: { min: 6.5, max: 7.5, optimal: 7, unit: 'pH', description: 'Soil acidity' },
      ec: { min: 1.0, max: 3.0, optimal: 2.0, unit: 'mS/cm', description: 'Nutrient concentration' }
    };
  }

  // Calculate NPK from EC and pH
  calculateNPKFromECpH(ec, ph) {
    // More realistic formulas for lavender
    return {
      nitrogen: Math.min(100, Math.max(0, (ec * 25) + ((ph - 6.0) * 10))),
      phosphorus: Math.min(100, Math.max(0, (ec * 15) + ((7.0 - Math.abs(7.0 - ph)) * 15))),
      potassium: Math.min(100, Math.max(0, (ec * 20) + ((ph - 6.5) * 12)))
    };
  }

  // MAIN INTELLIGENT DIAGNOSIS ENGINE
  analyzeSituation(aiResult, sensorData) {
    console.log('🧠 Starting intelligent diagnosis...');
    console.log(`📸 CNN sees: ${aiResult.prediction} (${(aiResult.confidence * 100).toFixed(1)}% confidence)`);
    console.log(`📡 Sensors read:`, sensorData);

    const aiPrediction = aiResult.prediction;
    const aiConfidence = aiResult.confidence;
    
    // Step 1: Check if sensors are realistic or malfunctioning
    const sensorAssessment = this.assessSensorCredibility(sensorData);
    const sensorIssues = this.checkSensorValidity(sensorData);
    
    // Step 2: Calculate NPK from EC/pH if available
    let calculatedNPK = null;
    if (sensorData.ec !== undefined && sensorData.ph !== undefined) {
      calculatedNPK = this.calculateNPKFromECpH(sensorData.ec, sensorData.ph);
      console.log(`🧪 Calculated NPK from EC/pH:`, calculatedNPK);
    }
    
    // Step 3: Generate intelligent diagnosis
    let diagnosis = this.generateIntelligentDiagnosis(aiPrediction, aiConfidence, sensorData, sensorAssessment, calculatedNPK);
    
    // Step 4: Determine emergency level
    const emergencyLevel = this.determineEmergencyLevel(diagnosis, sensorAssessment);
    
    // Step 5: Generate actionable recommendations
    const recommendations = this.generateActionableRecommendations(diagnosis, sensorData, sensorAssessment, emergencyLevel);
    
    // Step 6: Identify specific deficiencies
    const deficiencies = this.identifySpecificDeficiencies(aiResult, sensorData, calculatedNPK);
    
    return {
      emergencyLevel,
      visualAssessment: {
        prediction: aiPrediction,
        confidence: aiConfidence,
        message: this.getVisualAssessmentMessage(aiPrediction, aiConfidence)
      },
      sensorAssessment: {
        ...sensorAssessment,
        readings: sensorData,
        calculatedNPK,
        issues: sensorIssues.issues
      },
      intelligentDiagnosis: diagnosis,
      deficiencies,
      recommendations,
      nextSteps: this.generateNextSteps(emergencyLevel, diagnosis.requiresImmediateAction)
    };
  }

  // Assess if sensors are credible or malfunctioning
  assessSensorCredibility(sensorData) {
    const allZero = Object.values(sensorData).every(val => val === 0 || val === 0.0);
    const allMax = Object.values(sensorData).every(val => {
      const key = Object.keys(sensorData).find(k => sensorData[k] === val);
      const standard = this.sensorStandards[key];
      return standard && val === 100;
    });
    
    if (allZero) {
      return {
        status: 'malfunctioning',
        message: '⚠️ SENSOR MALFUNCTION DETECTED: All sensors read 0',
        confidence: 'low',
        recommendation: 'Check sensor connections and power supply'
      };
    }
    
    if (allMax) {
      return {
        status: 'suspicious',
        message: '⚠️ SUSPICIOUS READINGS: All sensors at maximum values',
        confidence: 'medium',
        recommendation: 'Verify sensor calibration'
      };
    }
    
    const issues = this.checkSensorValidity(sensorData);
    return {
      status: issues.hasIssues ? 'needs_attention' : 'credible',
      message: issues.hasIssues ? 
        `${issues.issues.length} sensor(s) out of optimal range` : 
        'Sensor readings appear credible',
      confidence: 'high',
      recommendation: issues.hasIssues ? 'Adjust sensor values' : 'Sensors working properly'
    };
  }

  // Generate intelligent diagnosis
  generateIntelligentDiagnosis(aiPrediction, aiConfidence, sensorData, sensorAssessment, calculatedNPK) {
    const sensorIssues = this.checkSensorValidity(sensorData);
    
    // Case 1: CNN and sensors agree
    if ((aiPrediction === 'healthy' && !sensorIssues.hasIssues) || 
        (aiPrediction !== 'healthy' && sensorIssues.hasIssues)) {
      
      if (aiPrediction === 'healthy') {
        return {
          verdict: 'PLANT IS HEALTHY',
          confidence: 'very_high',
          message: `✅ Visual appearance (${(aiConfidence * 100).toFixed(1)}% confidence) confirms healthy plant. Sensors show optimal conditions.`,
          reasoning: 'Both visual indicators and sensor data agree on plant health.',
          requiresImmediateAction: false
        };
      } else if (aiPrediction === 'nutrient_deficient') {
        const deficiencies = this.detectNutrientDeficiencies(sensorData, calculatedNPK);
        return {
          verdict: 'NUTRIENT DEFICIENCY CONFIRMED',
          confidence: 'high',
          message: `⚠️ Visual symptoms (${(aiConfidence * 100).toFixed(1)}% confidence) match sensor-detected nutrient issues.`,
          reasoning: `CNN detected deficiency patterns matching ${deficiencies.length > 0 ? deficiencies.join(', ') : 'multiple nutrient'} imbalances.`,
          requiresImmediateAction: true
        };
      } else if (aiPrediction === 'diseased') {
        return {
          verdict: 'DISEASE DETECTED',
          confidence: 'high',
          message: `🚨 Visual analysis (${(aiConfidence * 100).toFixed(1)}% confidence) indicates disease. Sensor conditions may be contributing.`,
          reasoning: 'Plant shows visual disease symptoms that require immediate attention.',
          requiresImmediateAction: true
        };
      }
    }
    
    // Case 2: CNN says healthy but sensors show issues
    if (aiPrediction === 'healthy' && sensorIssues.hasIssues) {
      if (sensorAssessment.status === 'malfunctioning') {
        return {
          verdict: 'SENSOR MALFUNCTION',
          confidence: 'high',
          message: `✅ Plant appears healthy (${(aiConfidence * 100).toFixed(1)}% confidence) but sensors show malfunction.`,
          reasoning: 'Visual health indicators contradict sensor readings. Likely sensor hardware issue.',
          requiresImmediateAction: false
        };
      } else {
        return {
          verdict: 'EARLY WARNING',
          confidence: 'medium',
          message: `⚠️ Plant looks healthy (${(aiConfidence * 100).toFixed(1)}% confidence) but sensors show developing issues.`,
          reasoning: 'Sensors detect suboptimal conditions that may not yet show visual symptoms.',
          requiresImmediateAction: true
        };
      }
    }
    
    // Case 3: CNN shows issues but sensors say healthy
    if (aiPrediction !== 'healthy' && !sensorIssues.hasIssues) {
      return {
        verdict: 'VISUAL ISSUE DETECTED',
        confidence: 'medium',
        message: `🔍 CNN detects issues (${(aiConfidence * 100).toFixed(1)}% confidence) but sensors report normal conditions.`,
        reasoning: 'Visual symptoms detected that may not be related to measured soil conditions.',
        requiresImmediateAction: true
      };
    }
    
    return {
      verdict: 'INCONCLUSIVE',
      confidence: 'low',
      message: 'Analysis results are inconclusive. Further investigation needed.',
      reasoning: 'Conflicting signals between visual and sensor data.',
      requiresImmediateAction: false
    };
  }

  // Detect specific nutrient deficiencies
  detectNutrientDeficiencies(sensorData, calculatedNPK) {
    const deficiencies = [];
    const npkValues = calculatedNPK || sensorData;
    
    if (npkValues.nitrogen < 40) deficiencies.push('Nitrogen (N)');
    if (npkValues.phosphorus < 20) deficiencies.push('Phosphorus (P)');
    if (npkValues.potassium < 30) deficiencies.push('Potassium (K)');
    
    return deficiencies;
  }

  // Determine emergency level
  determineEmergencyLevel(diagnosis, sensorAssessment) {
    if (diagnosis.verdict.includes('DISEASE') || diagnosis.requiresImmediateAction) {
      return {
        level: 'high',
        color: 'red',
        icon: '🚨',
        message: 'IMMEDIATE ACTION REQUIRED'
      };
    }
    
    if (sensorAssessment.status === 'malfunctioning' || diagnosis.verdict.includes('WARNING')) {
      return {
        level: 'medium',
        color: 'orange',
        icon: '⚠️',
        message: 'ATTENTION NEEDED'
      };
    }
    
    return {
      level: 'low',
      color: 'green',
      icon: '✅',
      message: 'MONITOR REGULARLY'
    };
  }

  // Generate actionable recommendations
  generateActionableRecommendations(diagnosis, sensorData, sensorAssessment, emergencyLevel) {
    const recommendations = [];
    
    // Add emergency-specific actions
    if (emergencyLevel.level === 'high') {
      recommendations.push({
        action: 'ISOLATE PLANT',
        reason: 'Prevent spread to other plants',
        priority: 1,
        icon: '🚨'
      });
    }
    
    // Handle sensor malfunctions
    if (sensorAssessment.status === 'malfunctioning') {
      recommendations.push({
        action: 'CHECK SENSOR CONNECTIONS',
        reason: 'All sensors reading 0 - likely hardware issue',
        priority: 1,
        icon: '🔧'
      });
      return recommendations;
    }
    
    // Add nutrient-specific recommendations
    const deficiencies = this.detectNutrientDeficiencies(sensorData);
    deficiencies.forEach((def, index) => {
      recommendations.push({
        action: this.getNutrientAction(def),
        reason: `${def} deficiency detected`,
        priority: 2 + index,
        icon: '🌱'
      });
    });
    
    // Add water recommendations
    if (sensorData.moisture < 20) {
      recommendations.push({
        action: 'WATER IMMEDIATELY',
        reason: `Soil moisture at ${sensorData.moisture}% (optimal: 20-40%)`,
        priority: 2,
        icon: '💧'
      });
    } else if (sensorData.moisture > 40) {
      recommendations.push({
        action: 'REDUCE WATERING',
        reason: `Soil moisture at ${sensorData.moisture}% (optimal: 20-40%)`,
        priority: 2,
        icon: '⏱️'
      });
    }
    
    // Add pH adjustments
    if (sensorData.ph < 6.5) {
      recommendations.push({
        action: 'ADD LIME TO RAISE pH',
        reason: `Soil pH at ${sensorData.ph} (optimal: 6.5-7.5)`,
        priority: 3,
        icon: '🧪'
      });
    } else if (sensorData.ph > 7.5) {
      recommendations.push({
        action: 'ADD SULFUR TO LOWER pH',
        reason: `Soil pH at ${sensorData.ph} (optimal: 6.5-7.5)`,
        priority: 3,
        icon: '🧪'
      });
    }
    
    // Sort by priority
    return recommendations.sort((a, b) => a.priority - b.priority);
  }

  // Identify all deficiencies
  identifySpecificDeficiencies(aiResult, sensorData, calculatedNPK) {
    const deficiencies = [];
    
    // From CNN's possible_issues
    if (aiResult.possible_issues) {
      aiResult.possible_issues.forEach(issue => {
        deficiencies.push({
          type: 'visual',
          deficiency: issue.replace('_deficiency', '').toUpperCase(),
          detectedBy: 'CNN Model',
          confidence: aiResult.confidence
        });
      });
    }
    
    // From sensor readings
    const npkValues = calculatedNPK || sensorData;
    if (npkValues.nitrogen < 40) {
      deficiencies.push({
        type: 'sensor',
        deficiency: 'NITROGEN',
        level: npkValues.nitrogen,
        unit: 'ppm',
        detectedBy: 'Soil Sensor',
        severity: npkValues.nitrogen < 20 ? 'severe' : 'moderate'
      });
    }
    
    if (npkValues.phosphorus < 20) {
      deficiencies.push({
        type: 'sensor',
        deficiency: 'PHOSPHORUS',
        level: npkValues.phosphorus,
        unit: 'ppm',
        detectedBy: 'Soil Sensor',
        severity: npkValues.phosphorus < 10 ? 'severe' : 'moderate'
      });
    }
    
    if (npkValues.potassium < 30) {
      deficiencies.push({
        type: 'sensor',
        deficiency: 'POTASSIUM',
        level: npkValues.potassium,
        unit: 'ppm',
        detectedBy: 'Soil Sensor',
        severity: npkValues.potassium < 15 ? 'severe' : 'moderate'
      });
    }
    
    return deficiencies;
  }

  // Generate next steps
  generateNextSteps(emergencyLevel, requiresImmediateAction) {
    if (requiresImmediateAction) {
      return {
        title: '🔄 WHAT TO DO NEXT',
        steps: [
          '1. Review emergency actions below',
          '2. Implement highest priority recommendations first',
          '3. Take photos after treatment for comparison',
          '4. Re-analyze in 3-5 days'
        ],
        buttonText: emergencyLevel.level === 'high' ? '🚨 TAKE EMERGENCY ACTION' : '⚡ START RECOVERY PLAN'
      };
    }
    
    return {
      title: '📝 RECOMMENDED NEXT STEPS',
      steps: [
        '1. Review recommendations below',
        '2. Adjust care routine as suggested',
        '3. Monitor plant daily',
        '4. Re-analyze weekly for improvements'
      ],
      buttonText: '🌱 VIEW ACTION PLAN'
    };
  }

  // Helper methods
  checkSensorValidity(sensorData) {
    const issues = [];
    
    Object.entries(sensorData).forEach(([key, value]) => {
      const standard = this.sensorStandards[key];
      if (standard && (value < standard.min || value > standard.max)) {
        issues.push({
          sensor: key,
          value: value,
          unit: standard.unit,
          min: standard.min,
          max: standard.max,
          severity: value < standard.min ? 'low' : 'high'
        });
      }
    });
    
    return {
      hasIssues: issues.length > 0,
      issues: issues,
      message: issues.length === 0 ? 'All sensors optimal' : `${issues.length} sensor(s) need attention`
    };
  }

  getVisualAssessmentMessage(prediction, confidence) {
    const confidencePercent = (confidence * 100).toFixed(1);
    switch(prediction) {
      case 'healthy':
        return `The plant appears visually healthy with ${confidencePercent}% confidence.`;
      case 'nutrient_deficient':
        return `Visual symptoms suggest nutrient deficiency with ${confidencePercent}% confidence.`;
      case 'diseased':
        return `Disease symptoms detected with ${confidencePercent}% confidence.`;
      default:
        return `Visual analysis completed with ${confidencePercent}% confidence.`;
    }
  }

  getNutrientAction(deficiency) {
    switch(deficiency) {
      case 'Nitrogen (N)':
        return 'APPLY NITROGEN-RICH FERTILIZER (20-10-10)';
      case 'Phosphorus (P)':
        return 'ADD BONE MEAL OR ROCK PHOSPHATE';
      case 'Potassium (K)':
        return 'APPLY POTASH OR POTASSIUM SULFATE';
      default:
        return 'APPLY BALANCED FERTILIZER';
    }
  }
}

module.exports = DecisionEngine;