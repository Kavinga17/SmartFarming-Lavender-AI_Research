// lib/services/irrigation_service.dart
import 'package:flutter/foundation.dart';
import '../models/irrigation.dart';

class IrrigationService with ChangeNotifier {
  IrrigationSettings? _currentSettings;
  List<IrrigationCycle> _upcomingCycles = [];
  List<IrrigationCycle> _pastCycles = [];
  DiagnosticData? _latestDiagnostic;

  IrrigationSettings? get currentSettings => _currentSettings;
  List<IrrigationCycle> get upcomingCycles => _upcomingCycles;
  List<IrrigationCycle> get pastCycles => _pastCycles;
  DiagnosticData? get latestDiagnostic => _latestDiagnostic;

  // Initialize or update irrigation settings
  Future<void> initializeSettings({
    required int plantCount,
    PlantType plantType = PlantType.lavender,
    required String userId,
  }) async {
    _currentSettings = IrrigationSettings.initial(
      userId: userId,
      plantCount: plantCount,
      plantType: plantType,
    );

    // Generate initial schedule
    await _generateSchedule();

    notifyListeners();
  }

  // Generate irrigation schedule
  Future<void> _generateSchedule() async {
    if (_currentSettings == null) return;

    _upcomingCycles.clear();
    final now = DateTime.now();

    // Generate next 7 cycles
    for (int i = 0; i < 7; i++) {
      final scheduledTime = now.add(
        _currentSettings!.irrigationInterval * (i + 1),
      );

      // Apply diagnostic adjustments if available
      double waterAmount =
          _currentSettings!.waterAmountPerPlant * _currentSettings!.plantCount;
      Duration duration = _currentSettings!.irrigationDuration;

      if (_latestDiagnostic != null &&
          _latestDiagnostic!.condition != 'optimal') {
        final adjusted = _applyDiagnosticAdjustment(waterAmount, duration);
        waterAmount = adjusted['waterAmount'];
        duration = adjusted['duration'];
      }

      _upcomingCycles.add(
        IrrigationCycle(
          id: 'cycle_${now.millisecondsSinceEpoch}_$i',
          settingsId: _currentSettings!.id,
          scheduledTime: scheduledTime,
          waterAmount: waterAmount,
          duration: duration,
          status: IrrigationStatus.scheduled,
          isAdjusted:
              _latestDiagnostic != null &&
              _latestDiagnostic!.condition != 'optimal',
        ),
      );
    }

    notifyListeners();
  }

  // Apply diagnostic adjustments
  Map<String, dynamic> _applyDiagnosticAdjustment(
    double baseWaterAmount,
    Duration baseDuration,
  ) {
    if (_latestDiagnostic == null) {
      return {'waterAmount': baseWaterAmount, 'duration': baseDuration};
    }

    double adjustmentFactor = 1.0;
    Duration duration = baseDuration;

    switch (_latestDiagnostic!.condition) {
      case 'overwatered':
        adjustmentFactor = 0.6; // Reduce water by 40%
        // Also increase interval (handled in schedule generation)
        duration = Duration(seconds: (baseDuration.inSeconds * 0.6).ceil());
        break;
      case 'underwatered':
        adjustmentFactor = 1.4; // Increase water by 40%
        duration = Duration(seconds: (baseDuration.inSeconds * 1.4).ceil());
        break;
      default:
        adjustmentFactor = 1.0;
    }

    return {
      'waterAmount': baseWaterAmount * adjustmentFactor,
      'duration': duration,
    };
  }

  // Submit diagnostic data from moisture slider
  Future<void> submitDiagnosticData(double moistureLevel) async {
    String condition;
    String recommendation;
    Map<String, dynamic> adjustmentFactors;

    // Determine condition based on lavender requirements
    if (moistureLevel > 70) {
      condition = 'overwatered';
      recommendation = 'Reduce watering amount and increase interval';
      adjustmentFactors = {'waterReduction': 0.4, 'intervalIncrease': 1.5};
    } else if (moistureLevel < 30) {
      condition = 'underwatered';
      recommendation = 'Increase watering amount and reduce interval';
      adjustmentFactors = {'waterIncrease': 0.4, 'intervalReduction': 0.7};
    } else {
      condition = 'optimal';
      recommendation = 'Current irrigation schedule is optimal';
      adjustmentFactors = {'waterAdjustment': 0.0, 'intervalAdjustment': 0.0};
    }

    _latestDiagnostic = DiagnosticData(
      id: 'diag_${DateTime.now().millisecondsSinceEpoch}',
      settingsId: _currentSettings?.id ?? '',
      moistureLevel: moistureLevel,
      timestamp: DateTime.now(),
      condition: condition,
      recommendation: recommendation,
      adjustmentFactors: adjustmentFactors,
    );

    // Regenerate schedule with adjustments
    await _generateSchedule();

    notifyListeners();
  }

  // Manually trigger irrigation now
  Future<void> triggerIrrigationNow() async {
    if (_currentSettings == null) return;

    final now = DateTime.now();
    double waterAmount =
        _currentSettings!.waterAmountPerPlant * _currentSettings!.plantCount;
    Duration duration = _currentSettings!.irrigationDuration;

    // Apply diagnostic adjustments if needed
    if (_latestDiagnostic != null &&
        _latestDiagnostic!.condition != 'optimal') {
      final adjusted = _applyDiagnosticAdjustment(waterAmount, duration);
      waterAmount = adjusted['waterAmount'];
      duration = adjusted['duration'];
    }

    // Add to past cycles
    _pastCycles.insert(
      0,
      IrrigationCycle(
        id: 'manual_${now.millisecondsSinceEpoch}',
        settingsId: _currentSettings!.id,
        scheduledTime: now,
        actualTime: now,
        waterAmount: waterAmount,
        duration: duration,
        status: IrrigationStatus.completed,
        diagnosticNote: 'Manual trigger',
        isAdjusted:
            _latestDiagnostic != null &&
            _latestDiagnostic!.condition != 'optimal',
      ),
    );

    notifyListeners();
  }

  // Get next scheduled irrigation
  IrrigationCycle? getNextScheduled() {
    if (_upcomingCycles.isEmpty) return null;
    return _upcomingCycles.firstWhere(
      (cycle) => cycle.status == IrrigationStatus.scheduled,
      orElse: () => _upcomingCycles.first,
    );
  }

  // Calculate statistics
  Map<String, dynamic> getStatistics() {
    final totalWater = _pastCycles.fold(
      0.0,
      (sum, cycle) => sum + cycle.waterAmount,
    );

    final adjustedCycles = _pastCycles.where((c) => c.isAdjusted).length;

    return {
      'totalWaterUsed': totalWater,
      'totalCycles': _pastCycles.length,
      'adjustedCycles': adjustedCycles,
      'waterSaved': totalWater * 0.15, // Estimate
    };
  }
}
