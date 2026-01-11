// src/services/decisionEngine.js
class DecisionEngine {
  constructor() {
    // Adjusted for lavender (prefers drier conditions)
    this.sensorStandards = {
      nitrogen: { min: 40, max: 80, optimal: 60, unit: 'ppm', description: 'Leaf growth and color' },
      phosphorus: { min: 20, max: 50, optimal: 35, unit: 'ppm', description: 'Root and flower development' },
      potassium: { min: 30, max: 70, optimal: 50, unit: 'ppm', description: 'Disease resistance' },
      moisture: { min: 30, max: 50, optimal: 40, unit: '%', description: 'Soil water content' }, // Lavender prefers 30-50%
      temperature: { min: 15, max: 30, optimal: 22, unit: '°C', description: 'Ambient temperature' },
      ph: { min: 6.0, max: 7.5, optimal: 7.0, unit: 'pH', description: 'Soil acidity' }, // Lavender prefers neutral to slightly alkaline
      ec: { min: 1.0, max: 3.0, optimal: 2.0, unit: 'mS/cm', description: 'Nutrient concentration' }
    };
  }

  // Calculate NPK from EC and pH
  calculateNPKFromECpH(ec, ph) {
    return {
      nitrogen: Math.min(100, Math.max(0, (ec * 25) + ((ph - 6.0) * 10))),
      phosphorus: Math.min(100, Math.max(0, (ec * 15) + ((7.0 - Math.abs(7.0 - ph)) * 15))),
      potassium: Math.min(100, Math.max(0, (ec * 20) + ((ph - 6.5) * 12)))
    };
  }

  // FIXED: Cross-verification that makes sense
  crossVerifyDiagnosis(cnnPrediction, cnnConfidence, sensorData, sensorAssessment) {
    console.log('🔍 Cross-verification analysis:');
    console.log(`   CNN: ${cnnPrediction} (${(cnnConfidence * 100).toFixed(1)}% confidence)`);
    console.log(`   Moisture: ${sensorData.moisture}% (optimal: ${this.sensorStandards.moisture.min}-${this.sensorStandards.moisture.max}%)`);
    console.log(`   pH: ${sensorData.ph} (optimal: ${this.sensorStandards.ph.min}-${this.sensorStandards.ph.max})`);
    
    const crossVerification = {
      matchPercentage: 0,
      sensorCorrelation: {},
      conflicts: [],
      agreements: [],
      confidence: 'medium',
      overallStatus: 'needs_review'
    };

    let matchScore = 0;
    const totalMetrics = 3; // Simplified to 3 key metrics
    
    // METRIC 1: Basic health agreement
    const isHealthyByCNN = cnnPrediction === 'healthy';
    const sensorIssues = this.checkSensorValidity(sensorData);
    const isHealthyBySensors = !sensorIssues.hasIssues;
    
    if (isHealthyByCNN && isHealthyBySensors) {
      matchScore += 1;
      crossVerification.agreements.push('health_confirmed');
      console.log('   ✓ Both healthy - perfect match');
    } else if (!isHealthyByCNN && !isHealthyBySensors) {
      matchScore += 0.8;
      crossVerification.agreements.push('issues_confirmed');
      console.log('   ✓ Both detect issues');
    } else {
      // Conflict - but let's see if it's a false positive/negative
      if (isHealthyByCNN && !isHealthyBySensors) {
        crossVerification.conflicts.push({
          type: 'health_status',
          cnn: 'healthy',
          sensors: 'issues',
          message: 'Plant looks healthy but sensors show issues'
        });
        console.log('   ⚠️ Conflict: Healthy plant but sensors show issues');
      } else {
        crossVerification.conflicts.push({
          type: 'health_status',
          cnn: 'issues',
          sensors: 'healthy',
          message: 'Plant shows issues but sensors are optimal'
        });
        console.log('   ⚠️ Conflict: Plant shows issues but sensors are healthy');
      }
      matchScore += 0.3; // Partial match for conflicts
    }

    // METRIC 2: Specific issue correlation
    if (cnnPrediction === 'nutrient_deficient') {
      const npkIssues = this.checkNPKIssues(sensorData);
      if (npkIssues.length > 0) {
        matchScore += 1;
        crossVerification.agreements.push('nutrient_issues_confirmed');
        console.log(`   ✓ Nutrient deficiency confirmed: ${npkIssues.join(', ')}`);
      } else {
        crossVerification.conflicts.push({
          type: 'nutrient_deficiency',
          cnn: 'yes',
          sensors: 'no',
          message: 'CNN detects nutrient issues but sensors show normal NPK'
        });
        console.log('   ⚠️ Nutrient issue not confirmed by sensors');
        matchScore += 0.2;
      }
    }

    // METRIC 3: Watering correlation
    if (cnnPrediction.includes('over') || cnnPrediction === 'over_watering') {
      const moistureStatus = this.getMoistureStatus(sensorData.moisture);
      if (moistureStatus === 'high') {
        matchScore += 1;
        crossVerification.agreements.push('over_watering_confirmed');
        console.log('   ✓ Over-watering confirmed by moisture sensor');
      }
    } else if (cnnPrediction.includes('under') || cnnPrediction === 'under_watered') {
      const moistureStatus = this.getMoistureStatus(sensorData.moisture);
      if (moistureStatus === 'low') {
        matchScore += 1;
        crossVerification.agreements.push('under_watering_confirmed');
        console.log('   ✓ Under-watering confirmed by moisture sensor');
      }
    }

    // Apply CNN confidence weighting
    matchScore *= (cnnConfidence * 0.5 + 0.5); // Scale from 0.5 to 1.0 based on confidence

    // Calculate match percentage (0-100%)
    crossVerification.matchPercentage = Math.min(100, Math.round((matchScore / totalMetrics) * 100));
    
    // Determine confidence level
    if (crossVerification.matchPercentage >= 85) {
      crossVerification.confidence = 'very_high';
      crossVerification.overallStatus = 'confirmed';
    } else if (crossVerification.matchPercentage >= 70) {
      crossVerification.confidence = 'high';
      crossVerification.overallStatus = 'likely';
    } else if (crossVerification.matchPercentage >= 50) {
      crossVerification.confidence = 'medium';
      crossVerification.overallStatus = 'partial';
    } else {
      crossVerification.confidence = 'low';
      crossVerification.overallStatus = 'conflicting';
    }

    // Add sensor correlation data
    crossVerification.sensorCorrelation = {
      moisture: {
        value: sensorData.moisture,
        status: this.getMoistureStatus(sensorData.moisture),
        optimal: `${this.sensorStandards.moisture.min}-${this.sensorStandards.moisture.max}%`
      },
      ph: {
        value: sensorData.ph,
        status: this.getPHStatus(sensorData.ph),
        optimal: `${this.sensorStandards.ph.min}-${this.sensorStandards.ph.max}`
      },
      ec: sensorData.ec ? {
        value: sensorData.ec,
        status: this.getECStatus(sensorData.ec),
        optimal: `${this.sensorStandards.ec.min}-${this.sensorStandards.ec.max} mS/cm`
      } : null,
      temperature: {
        value: sensorData.temperature,
        status: this.getTemperatureStatus(sensorData.temperature),
        optimal: `${this.sensorStandards.temperature.min}-${this.sensorStandards.temperature.max}°C`
      }
    };

    console.log(`✅ Cross-verification: ${crossVerification.matchPercentage}% match`);
    console.log(`   Status: ${crossVerification.overallStatus}, Confidence: ${crossVerification.confidence}`);
    
    return crossVerification;
  }

  // FIXED: Calculate health score sensibly
  calculateHealthScore(sensorData, cnnPrediction, cnnConfidence) {
    let score = 100;
    const issues = this.checkSensorValidity(sensorData);
    
    // Deduct for sensor issues
    issues.issues.forEach(issue => {
      const deviation = Math.max(
        Math.abs(issue.value - this.sensorStandards[issue.sensor].optimal),
        0
      );
      const maxDeviation = Math.max(
        Math.abs(this.sensorStandards[issue.sensor].max - this.sensorStandards[issue.sensor].optimal),
        Math.abs(this.sensorStandards[issue.sensor].min - this.sensorStandards[issue.sensor].optimal)
      );
      
      // Deduct proportionally to deviation
      const deduction = (deviation / maxDeviation) * 25;
      score -= deduction;
    });

    // Adjust based on CNN prediction
    if (cnnPrediction !== 'healthy') {
      // More penalty for diseased than nutrient deficient
      const penalty = cnnPrediction === 'diseased' ? 40 : 25;
      score -= (penalty * (1 - cnnConfidence)); // Less penalty if CNN is uncertain
    }

    // Cap between 0 and 100 and round
    score = Math.max(0, Math.min(100, score));
    
    return Math.round(score);
  }

  // Generate dashboard summary
  generateDashboardSummary(intelligentDiagnosis, sensorData, crossVerification, healthScore, aiPrediction) {
    const isHealthy = intelligentDiagnosis.verdict.includes('HEALTHY');
    
    return {
      healthScore,
      emergencyLevel: intelligentDiagnosis.requiresImmediateAction ? 'high' : 
                     (crossVerification.conflicts.length > 0 ? 'medium' : 'low'),
      status: isHealthy ? 'optimal' : 'needs_attention',
      trend: 'stable',
      lastUpdated: new Date().toISOString(),
      
      insights: {
        whatsWorking: this.getWhatsWorking(sensorData, intelligentDiagnosis),
        needsAttention: this.getNeedsAttention(intelligentDiagnosis, sensorData),
        watchFor: this.getWatchForItems(aiPrediction),
        goal: isHealthy ? 'Maintain current health' : 'Restore optimal conditions'
      },
      
      reminders: this.generateReminders(intelligentDiagnosis, sensorData),
      
      sensorStatus: {
        moisture: this.getMoistureStatus(sensorData.moisture),
        ph: this.getPHStatus(sensorData.ph),
        temperature: this.getTemperatureStatus(sensorData.temperature),
        nutrients: this.getNutrientStatus(sensorData)
      }
    };
  }

  // Helper methods
  getMoistureStatus(moisture) {
    if (moisture < this.sensorStandards.moisture.min) return 'low';
    if (moisture > this.sensorStandards.moisture.max) return 'high';
    return 'optimal';
  }

  getPHStatus(ph) {
    if (ph < this.sensorStandards.ph.min) return 'acidic';
    if (ph > this.sensorStandards.ph.max) return 'alkaline';
    return 'optimal';
  }

  getECStatus(ec) {
    if (!ec) return 'unknown';
    if (ec < this.sensorStandards.ec.min) return 'low';
    if (ec > this.sensorStandards.ec.max) return 'high';
    return 'optimal';
  }

  getTemperatureStatus(temp) {
    if (temp < this.sensorStandards.temperature.min) return 'cold';
    if (temp > this.sensorStandards.temperature.max) return 'hot';
    return 'optimal';
  }

  getNutrientStatus(sensorData) {
    const npk = this.calculateNPKFromECpH(sensorData.ec || 2.0, sensorData.ph || 7.0);
    const issues = [];
    if (npk.nitrogen < 40) issues.push('low_nitrogen');
    if (npk.phosphorus < 20) issues.push('low_phosphorus');
    if (npk.potassium < 30) issues.push('low_potassium');
    return issues.length === 0 ? 'balanced' : 'deficient';
  }

  checkNPKIssues(sensorData) {
    const npk = this.calculateNPKFromECpH(sensorData.ec || 2.0, sensorData.ph || 7.0);
    const issues = [];
    if (npk.nitrogen < 40) issues.push('N');
    if (npk.phosphorus < 20) issues.push('P');
    if (npk.potassium < 30) issues.push('K');
    return issues;
  }

  getWhatsWorking(sensorData, intelligentDiagnosis) {
    const workingItems = [];
    
    // Check what's actually working based on diagnosis
    if (intelligentDiagnosis.verdict.includes('HEALTHY')) {
      workingItems.push('Overall plant health');
    }
    
    if (this.getMoistureStatus(sensorData.moisture) === 'optimal') workingItems.push('Watering schedule');
    if (this.getPHStatus(sensorData.ph) === 'optimal') workingItems.push('Soil pH balance');
    if (this.getTemperatureStatus(sensorData.temperature) === 'optimal') workingItems.push('Temperature');
    
    return workingItems.length > 0 ? 
           workingItems.join(', ') : 
           'Plant structure intact';
  }

  getNeedsAttention(intelligentDiagnosis, sensorData) {
    const needs = [];
    
    // Only add if diagnosis indicates issues
    if (intelligentDiagnosis.verdict.includes('DEFICIENCY')) needs.push('Nutrient levels');
    if (intelligentDiagnosis.verdict.includes('WATERING')) needs.push('Watering schedule');
    if (intelligentDiagnosis.verdict.includes('DISEASE')) needs.push('Disease management');
    
    // Check sensor issues if diagnosis doesn't cover them
    const sensorIssues = this.checkSensorValidity(sensorData);
    if (sensorIssues.hasIssues && !intelligentDiagnosis.verdict.includes('HEALTHY')) {
      sensorIssues.issues.forEach(issue => {
        needs.push(`${issue.sensor} level`);
      });
    }
    
    return needs.length > 0 ? 
           needs.join(', ') : 
           'None - all systems optimal';
  }

  getWatchForItems(cnnPrediction) {
    switch(cnnPrediction) {
      case 'healthy': 
        return ['Normal growth patterns', 'Maintain current watering schedule'];
      case 'nutrient_deficient': 
        return ['Leaf color changes', 'Slow growth', 'Poor flowering'];
      case 'over_watering': 
        return ['Yellowing leaves', 'Root rot signs', 'Wilting despite wet soil'];
      case 'under_watered': 
        return ['Wilting', 'Leaf curling', 'Dry crispy leaves'];
      case 'diseased':
        return ['Spreading spots', 'Unusual discoloration', 'Rapid deterioration'];
      default: 
        return ['Any new symptoms', 'Changes in growth pattern'];
    }
  }

  generateReminders(intelligentDiagnosis, sensorData) {
    const reminders = [];
    const now = new Date();
    
    // Only add reminders if there are actual issues
    if (!intelligentDiagnosis.verdict.includes('HEALTHY')) {
      // Watering reminder
      const moistureStatus = this.getMoistureStatus(sensorData.moisture);
      if (moistureStatus === 'low') {
        reminders.push({
          id: 'water_soon',
          title: 'Water in 12h',
          description: 'Soil moisture getting low',
          dueTime: new Date(now.getTime() + 12 * 60 * 60 * 1000),
          priority: 'medium',
          icon: '💧'
        });
      } else if (moistureStatus === 'high') {
        reminders.push({
          id: 'reduce_watering',
          title: 'Skip next watering',
          description: 'Soil moisture too high',
          dueTime: new Date(now.getTime() + 24 * 60 * 60 * 1000),
          priority: 'medium',
          icon: '⏱️'
        });
      }
    }
    
    // Always add analysis reminder
    reminders.push({
      id: 'next_analysis',
      title: 'Next analysis in 7 days',
      description: 'Schedule next diagnostic check',
      dueTime: new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000),
      priority: 'low',
      icon: '📅'
    });
    
    return reminders;
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
    
    // Step 4: Cross-verification analysis
    const crossVerification = this.crossVerifyDiagnosis(aiPrediction, aiConfidence, sensorData, sensorAssessment);
    
    // Step 5: Calculate health score for dashboard
    const healthScore = this.calculateHealthScore(sensorData, aiPrediction, aiConfidence);
    
    // Step 6: Generate dashboard summary
    const dashboardSummary = this.generateDashboardSummary(
      diagnosis, 
      sensorData, 
      crossVerification, 
      healthScore,
      aiPrediction
    );
    
    // Step 7: Determine emergency level
    const emergencyLevel = this.determineEmergencyLevel(diagnosis, sensorAssessment);
    
    // Step 8: Generate actionable recommendations
    const recommendations = this.generateActionableRecommendations(diagnosis, sensorData, sensorAssessment, emergencyLevel);
    
    // Step 9: Identify specific deficiencies
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
      crossVerification,
      dashboardSummary,
      deficiencies,
      recommendations,
      nextSteps: this.generateNextSteps(emergencyLevel, diagnosis.requiresImmediateAction),
      healthScore
    };
  }

  // FIXED: Generate intelligent diagnosis
  generateIntelligentDiagnosis(aiPrediction, aiConfidence, sensorData, sensorAssessment, calculatedNPK) {
    const sensorIssues = this.checkSensorValidity(sensorData);
    
    console.log('🧠 Diagnosis logic:');
    console.log(`   CNN: ${aiPrediction}, Sensor Issues: ${sensorIssues.hasIssues}`);
    
    // CASE 1: Both healthy - PERFECT
    if (aiPrediction === 'healthy' && !sensorIssues.hasIssues) {
      console.log('   ✓ Both healthy - returning HEALTHY diagnosis');
      return {
        verdict: 'PLANT IS HEALTHY',
        confidence: 'very_high',
        message: `✅ Plant appears healthy (${(aiConfidence * 100).toFixed(1)}% confidence). All sensors optimal.`,
        reasoning: 'Both visual indicators and sensor data confirm plant health.',
        requiresImmediateAction: false
      };
    }
    
    // CASE 2: CNN sees issues, sensors confirm
    if (aiPrediction !== 'healthy' && sensorIssues.hasIssues) {
      console.log(`   ✓ Issues confirmed by both CNN and sensors`);
      
      if (aiPrediction === 'nutrient_deficient') {
        const deficiencies = this.detectNutrientDeficiencies(sensorData, calculatedNPK);
        return {
          verdict: 'NUTRIENT DEFICIENCY CONFIRMED',
          confidence: 'high',
          message: `⚠️ Visual symptoms (${(aiConfidence * 100).toFixed(1)}% confidence) match sensor-detected nutrient issues.`,
          reasoning: `CNN detected deficiency patterns matching sensor NPK readings.`,
          requiresImmediateAction: true
        };
      } else if (aiPrediction.includes('over') || aiPrediction === 'over_watering') {
        return {
          verdict: 'OVER-WATERING DETECTED',
          confidence: 'high',
          message: `💧 Plant shows over-watering symptoms (${(aiConfidence * 100).toFixed(1)}% confidence). Moisture sensor confirms excess water.`,
          reasoning: 'Visual signs of over-watering match high soil moisture readings.',
          requiresImmediateAction: true
        };
      } else if (aiPrediction.includes('under') || aiPrediction === 'under_watered') {
        return {
          verdict: 'UNDER-WATERING DETECTED',
          confidence: 'high',
          message: `🌵 Plant shows under-watering symptoms (${(aiConfidence * 100).toFixed(1)}% confidence). Moisture sensor confirms dry soil.`,
          reasoning: 'Visual signs of under-watering match low soil moisture readings.',
          requiresImmediateAction: true
        };
      } else if (aiPrediction === 'diseased') {
        return {
          verdict: 'DISEASE DETECTED',
          confidence: 'high',
          message: `🚨 Disease symptoms detected (${(aiConfidence * 100).toFixed(1)}% confidence). Environmental conditions may be contributing.`,
          reasoning: 'Visual disease symptoms detected. Check sensor conditions.',
          requiresImmediateAction: true
        };
      }
    }
    
    // CASE 3: CNN says healthy but sensors show issues (early warning)
    if (aiPrediction === 'healthy' && sensorIssues.hasIssues) {
      console.log('   ⚠️ Early warning: Healthy plant but sensors show issues');
      
      if (sensorAssessment.status === 'malfunctioning') {
        return {
          verdict: 'SENSOR MALFUNCTION',
          confidence: 'medium',
          message: `🔧 Plant appears healthy (${(aiConfidence * 100).toFixed(1)}% confidence) but sensors show malfunction.`,
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
    
    // CASE 4: CNN shows issues but sensors say healthy (visual-only issue)
    if (aiPrediction !== 'healthy' && !sensorIssues.hasIssues) {
      console.log('   ⚠️ Visual-only issue: CNN detects issues but sensors are optimal');
      return {
        verdict: 'VISUAL ISSUE DETECTED',
        confidence: 'medium',
        message: `🔍 CNN detects ${aiPrediction.replace('_', ' ')} (${(aiConfidence * 100).toFixed(1)}% confidence) but sensors report normal conditions.`,
        reasoning: 'Visual symptoms detected that may not be related to measured soil conditions.',
        requiresImmediateAction: true
      };
    }
    
    // Default: Inconclusive
    console.log('   ❓ Inconclusive analysis');
    return {
      verdict: 'INCONCLUSIVE',
      confidence: 'low',
      message: 'Analysis results are inconclusive. Further investigation needed.',
      reasoning: 'Conflicting signals between visual and sensor data.',
      requiresImmediateAction: false
    };
  }

  // FIXED: Generate recommendations that make sense
  generateActionableRecommendations(diagnosis, sensorData, sensorAssessment, emergencyLevel) {
    const recommendations = [];
    
    console.log('📋 Generating recommendations...');
    console.log(`   Diagnosis: ${diagnosis.verdict}`);
    console.log(`   Emergency Level: ${emergencyLevel.level}`);
    
    // Handle healthy plants first
    if (diagnosis.verdict.includes('HEALTHY')) {
      console.log('   ✓ Healthy plant - minimal recommendations');
      recommendations.push({
        action: 'CONTINUE CURRENT CARE ROUTINE',
        reason: 'Plant is healthy - maintain optimal conditions',
        priority: 1,
        icon: '✅'
      });
      return recommendations;
    }
    
    // Handle sensor malfunctions
    if (sensorAssessment.status === 'malfunctioning') {
      console.log('   ⚠️ Sensor malfunction detected');
      recommendations.push({
        action: 'CHECK SENSOR CONNECTIONS',
        reason: 'Sensor readings appear malfunctioning - check hardware',
        priority: 1,
        icon: '🔧'
      });
      return recommendations;
    }
    
    // Only add "ISOLATE PLANT" for actual diseases
    if (diagnosis.verdict.includes('DISEASE')) {
      console.log('   🚨 Disease detected - adding isolation');
      recommendations.push({
        action: 'ISOLATE PLANT',
        reason: 'Prevent spread of potential disease to other plants',
        priority: 1,
        icon: '🚨'
      });
    }
    
    // Add water recommendations based on moisture
    const moistureStatus = this.getMoistureStatus(sensorData.moisture);
    if (moistureStatus === 'low') {
      console.log('   💧 Low moisture - add watering recommendation');
      recommendations.push({
        action: 'WATER THOROUGHLY',
        reason: `Soil moisture at ${sensorData.moisture}% (optimal: ${this.sensorStandards.moisture.min}-${this.sensorStandards.moisture.max}%)`,
        priority: 2,
        icon: '💧'
      });
    } else if (moistureStatus === 'high') {
      console.log('   ⏱️ High moisture - reduce watering');
      recommendations.push({
        action: 'REDUCE WATERING FREQUENCY',
        reason: `Soil moisture at ${sensorData.moisture}% (optimal: ${this.sensorStandards.moisture.min}-${this.sensorStandards.moisture.max}%)`,
        priority: 2,
        icon: '⏱️'
      });
    }
    
    // Add pH adjustments if needed
    const phStatus = this.getPHStatus(sensorData.ph);
    if (phStatus === 'acidic') {
      console.log('   🧪 Acidic pH - add lime');
      recommendations.push({
        action: 'ADD GARDEN LIME TO RAISE pH',
        reason: `Soil pH at ${sensorData.ph} (optimal: ${this.sensorStandards.ph.min}-${this.sensorStandards.ph.max})`,
        priority: 3,
        icon: '🧪'
      });
    } else if (phStatus === 'alkaline') {
      console.log('   🧪 Alkaline pH - add sulfur');
      recommendations.push({
        action: 'ADD SULFUR TO LOWER pH',
        reason: `Soil pH at ${sensorData.ph} (optimal: ${this.sensorStandards.ph.min}-${this.sensorStandards.ph.max})`,
        priority: 3,
        icon: '🧪'
      });
    }
    
    // Add nutrient-specific recommendations
    const deficiencies = this.detectNutrientDeficiencies(sensorData);
    if (deficiencies.length > 0) {
      console.log(`   🌱 Nutrient deficiencies: ${deficiencies.join(', ')}`);
      deficiencies.forEach((def, index) => {
        recommendations.push({
          action: this.getNutrientAction(def),
          reason: `${def} deficiency detected`,
          priority: 4 + index,
          icon: '🌱'
        });
      });
    }
    
    // Sort by priority
    const sortedRecs = recommendations.sort((a, b) => a.priority - b.priority);
    console.log(`   Total recommendations: ${sortedRecs.length}`);
    return sortedRecs;
  }

  // Keep all your existing methods from here on...
  // [COPY ALL YOUR EXISTING METHODS FROM detectNutrientDeficiencies() to the end of the file]
  // I'll note the key ones that need to stay:

  detectNutrientDeficiencies(sensorData, calculatedNPK) {
    const deficiencies = [];
    const npkValues = calculatedNPK || sensorData;
    
    if (npkValues.nitrogen < 40) deficiencies.push('Nitrogen (N)');
    if (npkValues.phosphorus < 20) deficiencies.push('Phosphorus (P)');
    if (npkValues.potassium < 30) deficiencies.push('Potassium (K)');
    
    return deficiencies;
  }

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

  identifySpecificDeficiencies(aiResult, sensorData, calculatedNPK) {
    const deficiencies = [];
    
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