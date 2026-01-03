import 'dart:convert';
import 'dart:async';
import 'dart:html' as html;
import 'package:image_picker/image_picker.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:5000';

  static Future<bool> testConnection() async {
    try {
      final response = await html.HttpRequest.request(
        '$baseUrl/health',
        method: 'GET',
      );
      return response.status == 200;
    } catch (e) {
      return false;
    }
  }

  static Future<Map<String, dynamic>> analyzePlant({
    required XFile image,
    required Map<String, dynamic> sensorData,
  }) async {
    print('🎯 Starting plant analysis...');

    // Create FormData
    final formData = html.FormData();

    // Read file as blob
    final bytes = await image.readAsBytes();
    final blob = html.Blob([bytes], 'image/jpeg');

    // Append file
    formData.appendBlob('image', blob, 'plant.jpg');

    // Append sensor data
    formData.append('sensorData', jsonEncode(sensorData));

    // Create request
    final request = html.HttpRequest();
    request.open('POST', '$baseUrl/api/analysis');

    final completer = Completer<Map<String, dynamic>>();

    request.onLoad.listen((event) {
      if (request.status == 200) {
        try {
          final response = jsonDecode(request.responseText!);
          completer.complete(response);
        } catch (e) {
          completer.completeError(Exception('JSON parse error: $e'));
        }
      } else {
        completer.completeError(
          Exception('Server error ${request.status}: ${request.responseText}'),
        );
      }
    });

    request.onError.listen((event) {
      completer.completeError(Exception('Network error'));
    });

    // Send request
    request.send(formData);

    return await completer.future;
  }
}
