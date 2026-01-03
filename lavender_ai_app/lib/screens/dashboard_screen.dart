import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../services/api_service.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  bool _backendConnected = false;
  bool _checkingConnection = false;
  bool _isAnalyzing = false;
  XFile? _selectedImage;
  final Map<String, dynamic> _sensorData = {
    'nitrogen': 65.0,
    'phosphorus': 42.0,
    'potassium': 58.0,
    'moisture': 32.0,
    'temperature': 25.0,
    'ph': 7.0,
    'ec': 2.5,
  };
  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _checkBackendConnection();
  }

  Future<void> _checkBackendConnection() async {
    if (_checkingConnection) return;

    setState(() {
      _checkingConnection = true;
    });

    final connected = await ApiService.testConnection();

    setState(() {
      _backendConnected = connected;
      _checkingConnection = false;
    });

    if (!connected) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('⚠️ Cannot connect to backend'),
          backgroundColor: Colors.orange,
          duration: Duration(seconds: 3),
        ),
      );
    }
  }

  Future<void> _pickImage() async {
    final XFile? image = await _picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 85,
    );

    if (image != null) {
      setState(() {
        _selectedImage = image;
      });
    }
  }

  Future<void> _takePhoto() async {
    final XFile? image = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 85,
    );

    if (image != null) {
      setState(() {
        _selectedImage = image;
      });
    }
  }

  // Helper method to safely parse numbers
  double _safeParseDouble(dynamic value) {
    if (value == null) return 0.0;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is String) return double.tryParse(value) ?? 0.0;
    return 0.0;
  }

  String _safeFormatPercentage(dynamic value) {
    final doubleVal = _safeParseDouble(value);
    return doubleVal.toStringAsFixed(1);
  }

  Future<void> _analyzePlant() async {
    if (_selectedImage == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select an image first'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    setState(() {
      _isAnalyzing = true;
    });

    try {
      final result = await ApiService.analyzePlant(
        image: _selectedImage!,
        sensorData: _sensorData,
      );

      // Show results dialog - UPDATED with new format
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(
            result['mode'] == 'ai'
                ? '🤖 Intelligent Analysis Complete'
                : '🧪 Mock Analysis',
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ==================== 1. EMERGENCY LEVEL ====================
                if (result['intelligentDiagnosis']?['emergencyLevel'] != null)
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: _getEmergencyColor(
                        result['intelligentDiagnosis']['emergencyLevel']['level'],
                      ),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Text(
                          result['intelligentDiagnosis']['emergencyLevel']['icon'] ??
                              '⚠️',
                          style: const TextStyle(fontSize: 24),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            result['intelligentDiagnosis']['emergencyLevel']['message'] ??
                                'Analysis Complete',
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                const SizedBox(height: 20),

                // ==================== 2. VISUAL ASSESSMENT ====================
                const Text(
                  '👁️ VISUAL ASSESSMENT',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.blue,
                  ),
                ),
                const SizedBox(height: 10),

                if (result['visualAssessment'] != null)
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'CNN Model sees: ${result['visualAssessment']['cnnPrediction']?.toString().replaceAll('_', ' ').toUpperCase() ?? 'UNKNOWN'}',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 5),
                      Text(
                        'Confidence: ${_safeFormatPercentage(result['visualAssessment']['confidencePercentage'] ?? result['visualAssessment']['confidence'])}%',
                        style: TextStyle(
                          color: Colors.grey[700],
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(height: 5),
                      Text(
                        '💬 ${result['visualAssessment']['message'] ?? "Visual analysis complete"}',
                        style: const TextStyle(fontStyle: FontStyle.italic),
                      ),
                      const SizedBox(height: 10),
                    ],
                  ),

                // ==================== 3. SENSOR READINGS ====================
                const Divider(),
                const SizedBox(height: 10),
                const Text(
                  '📡 SENSOR READINGS',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.green,
                  ),
                ),
                const SizedBox(height: 10),

                // Sensor credibility
                if (result['sensorReadings']?['assessment'] != null)
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            result['sensorReadings']['assessment']['status'] ==
                                    'credible'
                                ? Icons.check_circle
                                : Icons.warning,
                            color:
                                result['sensorReadings']['assessment']['status'] ==
                                    'credible'
                                ? Colors.green
                                : Colors.orange,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              result['sensorReadings']['assessment']['message'] ??
                                  'Sensor status unknown',
                              style: TextStyle(
                                fontWeight: FontWeight.w500,
                                color:
                                    result['sensorReadings']['assessment']['status'] ==
                                        'credible'
                                    ? Colors.green
                                    : Colors.orange,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 5),

                      // Sensor issues
                      if (result['sensorReadings']['issues'] != null &&
                          result['sensorReadings']['issues'].isNotEmpty)
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              '⚠️ Issues detected:',
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                            ...result['sensorReadings']['issues']
                                .map<Widget>(
                                  (issue) => Text(
                                    '• ${issue['sensor']}: ${issue['value']}${issue['unit']} (optimal: ${issue['optimalRange']})',
                                    style: const TextStyle(fontSize: 13),
                                  ),
                                )
                                .toList(),
                          ],
                        ),

                      // Calculated NPK
                      if (result['sensorReadings']['calculatedNPK'] != null)
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const SizedBox(height: 10),
                            const Text(
                              '🧪 Calculated NPK Levels:',
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceAround,
                              children: [
                                _buildNpkItem(
                                  'N',
                                  result['sensorReadings']['calculatedNPK']['nitrogen'],
                                ),
                                _buildNpkItem(
                                  'P',
                                  result['sensorReadings']['calculatedNPK']['phosphorus'],
                                ),
                                _buildNpkItem(
                                  'K',
                                  result['sensorReadings']['calculatedNPK']['potassium'],
                                ),
                              ],
                            ),
                          ],
                        ),
                    ],
                  ),
                const SizedBox(height: 10),

                // ==================== 4. INTELLIGENT DIAGNOSIS ====================
                const Divider(),
                const SizedBox(height: 10),
                const Text(
                  '🧠 INTELLIGENT DIAGNOSIS',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.purple,
                  ),
                ),
                const SizedBox(height: 10),

                if (result['intelligentDiagnosis'] != null)
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Colors.grey[100],
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: Colors.grey[300]!,
                          ), // FIXED: Added !
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              result['intelligentDiagnosis']['verdict'] ??
                                  'NO VERDICT',
                              style: const TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: Colors.red,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              result['intelligentDiagnosis']['message'] ??
                                  'Analysis complete',
                              style: const TextStyle(fontSize: 15),
                            ),
                            const SizedBox(height: 8),
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: Colors.blue[50],
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                '🤔 Reasoning: ${result['intelligentDiagnosis']['reasoning'] ?? "No reasoning provided"}',
                                style: const TextStyle(fontSize: 13),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 15),
                    ],
                  ),

                // ==================== 5. SPECIFIC DEFICIENCIES ====================
                if (result['deficiencies'] != null &&
                    result['deficiencies'].isNotEmpty)
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        '⚠️ SPECIFIC DEFICIENCIES DETECTED',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.orange,
                        ),
                      ),
                      const SizedBox(height: 8),
                      ...result['deficiencies']
                          .map<Widget>(
                            (def) => Card(
                              margin: const EdgeInsets.symmetric(vertical: 4),
                              child: Padding(
                                padding: const EdgeInsets.all(8.0),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        const Icon(
                                          Icons.warning,
                                          color: Colors.orange,
                                          size: 16,
                                        ),
                                        const SizedBox(width: 8),
                                        Text(
                                          def['deficiency']
                                                  ?.toString()
                                                  .toUpperCase() ??
                                              'UNKNOWN',
                                          style: const TextStyle(
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                        const Spacer(),
                                        Text(
                                          'Detected by: ${def['detectedBy'] ?? 'Unknown'}',
                                          style: TextStyle(
                                            fontSize: 12,
                                            color: Colors.grey[600],
                                          ),
                                        ),
                                      ],
                                    ),
                                    if (def['level'] != null)
                                      Padding(
                                        padding: const EdgeInsets.only(
                                          left: 24,
                                        ),
                                        child: Text(
                                          'Level: ${def['level']}${def['unit'] ?? ''} ${def['severity'] != null ? '(${def['severity']})' : ''}',
                                          style: const TextStyle(fontSize: 13),
                                        ),
                                      ),
                                  ],
                                ),
                              ),
                            ),
                          )
                          .toList(),
                      const SizedBox(height: 15),
                    ],
                  ),

                // ==================== 6. ACTIONABLE RECOMMENDATIONS ====================
                if (result['recommendations'] != null &&
                    result['recommendations']['priorityOrder'] != null)
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Divider(),
                      const SizedBox(height: 10),
                      const Text(
                        '⚡ ACTION PLAN',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.red,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Priority: ${result['recommendations']['emergencyLevel']?.toString().toUpperCase() ?? 'LOW'}',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: _getEmergencyColor(
                            result['recommendations']['emergencyLevel'],
                          ),
                        ),
                      ),
                      const SizedBox(height: 10),
                      ...result['recommendations']['priorityOrder']
                          .map<Widget>(
                            (step) => Card(
                              margin: const EdgeInsets.symmetric(vertical: 4),
                              color: step['priority'] == 1
                                  ? Colors.red[50]
                                  : Colors.grey[50],
                              child: Padding(
                                padding: const EdgeInsets.all(10.0),
                                child: Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Container(
                                      width: 28,
                                      height: 28,
                                      decoration: BoxDecoration(
                                        color: step['priority'] == 1
                                            ? Colors.red
                                            : Colors.blue,
                                        shape: BoxShape.circle,
                                      ),
                                      child: Center(
                                        child: Text(
                                          step['step'].toString(),
                                          style: const TextStyle(
                                            color: Colors.white,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 12),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            '${step['icon'] ?? '👉'} ${step['action']}',
                                            style: const TextStyle(
                                              fontWeight: FontWeight.bold,
                                            ),
                                          ),
                                          const SizedBox(height: 4),
                                          Text(
                                            step['reason'] ??
                                                'Recommended action',
                                            style: TextStyle(
                                              fontSize: 13,
                                              color: Colors.grey[700],
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          )
                          .toList(),
                      const SizedBox(height: 15),
                    ],
                  ),

                // ==================== 7. WHAT TO DO NEXT ====================
                if (result['nextSteps'] != null)
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Divider(),
                      const SizedBox(height: 10),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.green[50],
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.green),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              result['nextSteps']['title'] ?? '📝 NEXT STEPS',
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: Colors.green,
                              ),
                            ),
                            const SizedBox(height: 8),
                            ...(result['nextSteps']['steps'] as List?)
                                    ?.map<Widget>(
                                      (step) => Padding(
                                        padding: const EdgeInsets.symmetric(
                                          vertical: 2,
                                        ),
                                        child: Row(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                            const Icon(
                                              Icons.arrow_right,
                                              size: 16,
                                              color: Colors.green,
                                            ),
                                            const SizedBox(width: 8),
                                            Expanded(
                                              child: Text(step.toString()),
                                            ),
                                          ],
                                        ),
                                      ),
                                    )
                                    .toList() ??
                                [],
                          ],
                        ),
                      ),
                      const SizedBox(height: 15),

                      // Action Button
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: () {
                            Navigator.pop(context);
                            // Show action plan in more detail
                            _showActionPlan(result);
                          },
                          icon: const Icon(Icons.task),
                          label: Text(
                            result['nextSteps']['buttonText'] ??
                                'VIEW ACTION PLAN',
                          ),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.green,
                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                        ),
                      ),
                    ],
                  ),

                // ==================== LEGACY SUPPORT ====================
                if (!result.containsKey('intelligentDiagnosis') &&
                    result.containsKey('finalDiagnosis'))
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        '⚠️ Using Legacy Format',
                        style: TextStyle(color: Colors.orange),
                      ),
                      const SizedBox(height: 10),
                      const Text(
                        'AI Diagnosis:',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                          color: Colors.green,
                        ),
                      ),
                      Text(
                        '🔍 ${result['finalDiagnosis']['health']?.toString().replaceAll('_', ' ').toUpperCase() ?? 'Unknown'}',
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if (result['finalDiagnosis']['issues'] != null &&
                          result['finalDiagnosis']['issues'] is List)
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const SizedBox(height: 10),
                            const Text(
                              '⚠️ Issues:',
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                            ...(result['finalDiagnosis']['issues'] as List)
                                .map(
                                  (issue) => Text(
                                    '• ${issue.toString().replaceAll('_', ' ')}',
                                  ),
                                )
                                ,
                          ],
                        ),
                    ],
                  ),

                const SizedBox(height: 20),
                const Divider(),
                Text(
                  'Mode: ${result['mode']} | Backend: localhost:5000',
                  style: TextStyle(color: Colors.grey[600], fontSize: 12),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        ),
      );
    } catch (e) {
      // Show detailed error
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('❌ Analysis Failed'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Error: $e'),
                const SizedBox(height: 15),
                const Text(
                  'Possible issues:',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const Text('1. Backend not running'),
                const Text('2. CORS not enabled on backend'),
                const Text('3. Invalid image format'),
                const Text('4. Network connectivity issue'),
                const SizedBox(height: 15),
                const Text(
                  'Check your backend server at:',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                Text('http://localhost:5000'),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('OK'),
            ),
          ],
        ),
      );
    } finally {
      setState(() {
        _isAnalyzing = false;
      });
    }
  }

  void _showActionPlan(Map<String, dynamic> result) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('📋 Detailed Action Plan'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (result['intelligentDiagnosis'] != null)
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      result['intelligentDiagnosis']['verdict'] ?? 'NO VERDICT',
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Colors.red,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(result['intelligentDiagnosis']['message'] ?? ''),
                    const SizedBox(height: 20),
                  ],
                ),

              if (result['recommendations']?['priorityOrder'] != null)
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Prioritized Actions:',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 10),
                    ...result['recommendations']['priorityOrder']
                        .map<Widget>(
                          (step) => Padding(
                            padding: const EdgeInsets.symmetric(vertical: 8),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  width: 30,
                                  height: 30,
                                  decoration: BoxDecoration(
                                    color: step['priority'] == 1
                                        ? Colors.red
                                        : Colors.blue,
                                    shape: BoxShape.circle,
                                  ),
                                  child: Center(
                                    child: Text(
                                      step['step'].toString(),
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        step['action'],
                                        style: const TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 15,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        step['reason'],
                                        style: TextStyle(
                                          color: Colors.grey[700],
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        'Priority: ${step['priority']}',
                                        style: TextStyle(
                                          fontSize: 12,
                                          color: Colors.grey[600],
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        )
                        .toList(),
                  ],
                ),

              const SizedBox(height: 20),
              const Text(
                '💡 Tips:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const Text('• Complete actions in order'),
              const Text('• Monitor plant daily'),
              const Text('• Take photos for comparison'),
              const Text('• Re-analyze in 3-5 days'),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Done'),
          ),
        ],
      ),
    );
  }

  // Helper methods
  Color _getEmergencyColor(String? level) {
    switch (level?.toLowerCase()) {
      case 'high':
        return Colors.red;
      case 'medium':
        return Colors.orange;
      case 'low':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  Widget _buildNpkItem(String label, dynamic value) {
    final doubleVal = _safeParseDouble(value);
    return Column(
      children: [
        Text(
          label,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        Text(
          doubleVal.toStringAsFixed(1),
          style: const TextStyle(fontSize: 14),
        ),
        Text('ppm', style: TextStyle(fontSize: 12, color: Colors.grey[600])),
      ],
    );
  }

  Widget _buildConnectionStatus() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: _backendConnected
            ? Colors.green.shade100
            : Colors.orange.shade100,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: _backendConnected ? Colors.green : Colors.orange,
          width: 1,
        ),
      ),
      child: Row(
        children: [
          _checkingConnection
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.blue,
                  ),
                )
              : Icon(
                  _backendConnected ? Icons.check_circle : Icons.warning,
                  color: _backendConnected ? Colors.green : Colors.orange,
                  size: 20,
                ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              _checkingConnection
                  ? 'Checking backend connection...'
                  : _backendConnected
                  ? '✅ Backend Connected (localhost:5000)'
                  : '⚠️ Backend Disconnected',
              style: TextStyle(
                color: _backendConnected ? Colors.green : Colors.orange,
                fontWeight: FontWeight.bold,
                fontSize: 14,
              ),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.refresh, size: 18),
            onPressed: _checkingConnection ? null : _checkBackendConnection,
            color: _backendConnected ? Colors.green : Colors.orange,
            tooltip: 'Recheck connection',
          ),
        ],
      ),
    );
  }

  Widget _buildSensorSlider(
    String title,
    String key,
    String unit,
    double min,
    double max,
  ) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: Slider(
                    value: _sensorData[key],
                    min: min,
                    max: max,
                    divisions: 20,
                    onChanged: (value) {
                      setState(() {
                        _sensorData[key] = double.parse(
                          value.toStringAsFixed(1),
                        );
                      });
                    },
                    activeColor: const Color.fromARGB(255, 20, 118, 47),
                  ),
                ),
                const SizedBox(width: 10),
                Text(
                  '${_sensorData[key]}$unit',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text('🌿 Lavender Dashboard'),
        centerTitle: true,
        backgroundColor: const Color.fromARGB(255, 20, 118, 47),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _checkBackendConnection,
            tooltip: 'Check backend connection',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildConnectionStatus(),
            const SizedBox(height: 20),

            const Text(
              'Test Sensor Values',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'Adjust sliders to simulate different conditions',
              style: TextStyle(color: Colors.grey, fontSize: 14),
            ),
            const SizedBox(height: 16),

            _buildSensorSlider('Nitrogen (N)', 'nitrogen', ' ppm', 0, 100),
            _buildSensorSlider('Phosphorus (P)', 'phosphorus', ' ppm', 0, 100),
            _buildSensorSlider('Potassium (K)', 'potassium', ' ppm', 0, 100),
            _buildSensorSlider('Soil Moisture', 'moisture', '%', 0, 100),
            _buildSensorSlider('pH Level', 'ph', ' pH', 0, 14),
            _buildSensorSlider(
              'EC (Electrical Conductivity)',
              'ec',
              ' mS/cm',
              0,
              5,
            ),

            const SizedBox(height: 25),

            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Plant Image',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      'Upload a photo of your lavender plant',
                      style: TextStyle(color: Colors.grey),
                    ),
                    const SizedBox(height: 16),

                    Container(
                      height: 200,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: Colors.grey[200],
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.grey),
                      ),
                      child: _selectedImage != null
                          ? ClipRRect(
                              borderRadius: BorderRadius.circular(10),
                              child: Image.network(
                                _selectedImage!.path,
                                fit: BoxFit.cover,
                                loadingBuilder:
                                    (context, child, loadingProgress) {
                                      if (loadingProgress == null) return child;
                                      return Center(
                                        child: CircularProgressIndicator(
                                          value:
                                              loadingProgress
                                                      .expectedTotalBytes !=
                                                  null
                                              ? loadingProgress
                                                        .cumulativeBytesLoaded /
                                                    loadingProgress
                                                        .expectedTotalBytes!
                                              : null,
                                        ),
                                      );
                                    },
                              ),
                            )
                          : const Center(
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(
                                    Icons.photo,
                                    size: 60,
                                    color: Colors.grey,
                                  ),
                                  SizedBox(height: 10),
                                  Text('No image selected'),
                                ],
                              ),
                            ),
                    ),

                    const SizedBox(height: 16),

                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: _pickImage,
                            icon: const Icon(Icons.photo_library),
                            label: const Text('Gallery'),
                            style: OutlinedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              side: BorderSide(
                                color: const Color.fromARGB(255, 20, 118, 47),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: _takePhoto,
                            icon: const Icon(Icons.camera_alt),
                            label: const Text('Camera'),
                            style: OutlinedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              side: BorderSide(
                                color: const Color.fromARGB(255, 20, 118, 47),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 25),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isAnalyzing ? null : _analyzePlant,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color.fromARGB(255, 20, 118, 47),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
                child: _isAnalyzing
                    ? const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          ),
                          SizedBox(width: 10),
                          Text(
                            'ANALYZING...',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      )
                    : const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.psychology, size: 24),
                          SizedBox(width: 10),
                          Text(
                            'ANALYZE PLANT',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
              ),
            ),

            const SizedBox(height: 25),

            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    const Text(
                      '🌱 Intelligent Plant Analysis',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      'Now featuring intelligent cross-checking between AI vision and sensor data for more accurate diagnoses.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey),
                    ),
                    const SizedBox(height: 10),
                    ElevatedButton.icon(
                      onPressed: _checkBackendConnection,
                      icon: const Icon(Icons.link),
                      label: const Text('Test Backend Connection'),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _checkBackendConnection,
        backgroundColor: const Color.fromARGB(255, 20, 118, 47),
        tooltip: 'Check backend connection',
        child: const Icon(Icons.link),
      ),
    );
  }
}
