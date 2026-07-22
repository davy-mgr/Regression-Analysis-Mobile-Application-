import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const StuntingPredictorApp());
}

class StuntingPredictorApp extends StatelessWidget {
  const StuntingPredictorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Stunting Predictor',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF2E7D6B)),
        useMaterial3: true,
        inputDecorationTheme: const InputDecorationTheme(
          border: OutlineInputBorder(),
          filled: true,
        ),
      ),
      home: const PredictionPage(),
    );
  }
}

class PredictionPage extends StatefulWidget {
  const PredictionPage({super.key});

  @override
  State<PredictionPage> createState() => _PredictionPageState();
}

class _PredictionPageState extends State<PredictionPage> {
  // -------------------------------------------------------------------
  // IMPORTANT: replace with your own deployed Render URL if it changes.
  // -------------------------------------------------------------------
  static const String apiBaseUrl =
      'https://regression-analysis-mobile-application-1ab3.onrender.com';

  final _formKey = GlobalKey<FormState>();

  final _genderController = TextEditingController();
  final _heightController = TextEditingController();
  final _zscoreWaController = TextEditingController();
  final _zscoreWhController = TextEditingController();

  bool _isLoading = false;
  String? _resultText;
  String? _errorText;

  @override
  void dispose() {
    _genderController.dispose();
    _heightController.dispose();
    _zscoreWaController.dispose();
    _zscoreWhController.dispose();
    super.dispose();
  }

  // ---- Validators mirror the API's Pydantic range constraints ----
  String? _validateGender(String? value) {
    if (value == null || value.trim().isEmpty) return 'Required';
    final parsed = int.tryParse(value.trim());
    if (parsed == null) return 'Must be a whole number';
    if (parsed < 0 || parsed > 1) return 'Must be 0 or 1';
    return null;
  }

  String? _validateHeight(String? value) {
    if (value == null || value.trim().isEmpty) return 'Required';
    final parsed = double.tryParse(value.trim());
    if (parsed == null) return 'Must be a number';
    if (parsed < 44.0 || parsed > 120.0) return 'Must be between 44.0 and 120.0 cm';
    return null;
  }

  String? _validateZScore(String? value, String label) {
    if (value == null || value.trim().isEmpty) return 'Required';
    final parsed = double.tryParse(value.trim());
    if (parsed == null) return 'Must be a number';
    if (parsed < -6.0 || parsed > 6.0) return 'Must be between -6.0 and 6.0';
    return null;
  }

  Future<void> _submitPrediction() async {
    setState(() {
      _resultText = null;
      _errorText = null;
    });

    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() => _isLoading = true);

    final requestBody = {
      'gender': int.parse(_genderController.text.trim()),
      'height': double.parse(_heightController.text.trim()),
      'zscore_wa': double.parse(_zscoreWaController.text.trim()),
      'zscore_wh': double.parse(_zscoreWhController.text.trim()),
    };

    try {
      final response = await http
          .post(
            Uri.parse('$apiBaseUrl/predict'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(requestBody),
          )
          .timeout(const Duration(seconds: 60));
      // 60s timeout: Render's free tier can take ~30-60s to wake up
      // from idle on the first request.

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final zscore = data['predicted_zscore_ha'];
        final risk = data['stunting_risk'];
        setState(() {
          _resultText =
              'Predicted Height-for-Age Z-Score: $zscore\nRisk category: $risk';
        });
      } else if (response.statusCode == 422) {
        setState(() {
          _errorText =
              'One or more values were out of the expected range. Please check your inputs.';
        });
      } else {
        setState(() {
          _errorText = 'Server error (${response.statusCode}). Please try again.';
        });
      }
    } catch (e) {
      setState(() {
        _errorText = 'Could not reach the server. Check your connection and try again.';
      });
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Stunting Predictor'),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Form(
                key: _formKey,
                autovalidateMode: AutovalidateMode.onUserInteraction,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text(
                      'Enter the child\'s measurements to predict '
                      'Height-for-Age Z-Score.',
                      style: TextStyle(fontSize: 15, color: Colors.black54),
                    ),
                    const SizedBox(height: 24),

                    TextFormField(
                      controller: _genderController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: 'Gender (0 or 1)',
                        helperText: 'As coded in the source dataset',
                        prefixIcon: Icon(Icons.person_outline),
                      ),
                      validator: _validateGender,
                    ),
                    const SizedBox(height: 16),

                    TextFormField(
                      controller: _heightController,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      decoration: const InputDecoration(
                        labelText: 'Height (cm)',
                        helperText: 'Valid range: 44.0 - 120.0',
                        prefixIcon: Icon(Icons.height),
                      ),
                      validator: _validateHeight,
                    ),
                    const SizedBox(height: 16),

                    TextFormField(
                      controller: _zscoreWaController,
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                        signed: true,
                      ),
                      decoration: const InputDecoration(
                        labelText: 'Weight-for-Age Z-Score',
                        helperText: 'Valid range: -6.0 to 6.0',
                        prefixIcon: Icon(Icons.monitor_weight_outlined),
                      ),
                      validator: (v) => _validateZScore(v, 'Weight-for-Age'),
                    ),
                    const SizedBox(height: 16),

                    TextFormField(
                      controller: _zscoreWhController,
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                        signed: true,
                      ),
                      decoration: const InputDecoration(
                        labelText: 'Weight-for-Height Z-Score',
                        helperText: 'Valid range: -6.0 to 6.0',
                        prefixIcon: Icon(Icons.accessibility_new),
                      ),
                      validator: (v) => _validateZScore(v, 'Weight-for-Height'),
                    ),
                    const SizedBox(height: 28),

                    FilledButton(
                      onPressed: _isLoading ? null : _submitPrediction,
                      style: FilledButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                      ),
                      child: _isLoading
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(strokeWidth: 2.5),
                            )
                          : const Text('Predict'),
                    ),
                    const SizedBox(height: 24),

                    // ---- Display area: result or error ----
                    if (_resultText != null)
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: const Color(0xFFE6F4EF),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: const Color(0xFF2E7D6B)),
                        ),
                        child: Text(
                          _resultText!,
                          style: const TextStyle(fontSize: 15, height: 1.5),
                        ),
                      ),
                    if (_errorText != null)
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFDECEA),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: const Color(0xFFB3261E)),
                        ),
                        child: Text(
                          _errorText!,
                          style: const TextStyle(fontSize: 15, color: Color(0xFFB3261E)),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
