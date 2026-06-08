import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';
import 'dart:ui';

void main() {
  runApp(const ChitraApp());
}

class ChitraApp extends StatelessWidget {
  const ChitraApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Chitra Voice Assistant',
      theme: ThemeData.light().copyWith(
        primaryColor: const Color(0xFFFFB300), // Amber accent
      ),
      home: const ChitraHomeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class ChitraHomeScreen extends StatefulWidget {
  const ChitraHomeScreen({super.key});

  @override
  State<ChitraHomeScreen> createState() => _ChitraHomeScreenState();
}

class _ChitraHomeScreenState extends State<ChitraHomeScreen>
    with TickerProviderStateMixin {
  late WebSocketChannel _channel;
  String _status = 'idle';
  String _message = 'Namaste. Press Ctrl+Shift+Space to speak.';

  late AnimationController _pulseController;
  late AnimationController _spinController;

  @override
  void initState() {
    super.initState();
    _connectToPython();

    // The breathing animation for when she listens
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    )..repeat(reverse: true);

    // The spinning animation for when she processes
    _spinController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();
  }

  void _connectToPython() {
    try {
      _channel = WebSocketChannel.connect(Uri.parse('ws://localhost:8765'));
      _channel.stream.listen(
        (message) {
          final Map<String, dynamic> data = jsonDecode(message);
          setState(() {
            _status = data['status'] ?? 'idle';
            _message = data['message'] ?? '';
          });
        },
        onError: (error) {
          setState(() => _message = 'Connection lost. Is Python running?');
        },
      );
    } catch (e) {
      setState(() => _message = 'Could not establish connection.');
    }
  }

  void _triggerMicRemotely() {
    if (_status != 'listening' && _status != 'transcribing') {
      _channel.sink.add(jsonEncode({"command": "start_mic"}));
    }
  }

  @override
  void dispose() {
    _channel.sink.close();
    _pulseController.dispose();
    _spinController.dispose();
    super.dispose();
  }

  // The Central Agent Animation
  Widget _buildAgentCore() {
    switch (_status) {
      case 'listening':
        return AnimatedBuilder(
          animation: _pulseController,
          builder: (context, child) {
            return Stack(
              alignment: Alignment.center,
              children: [
                // Outer glowing pulse
                Container(
                  width: 150 + (_pulseController.value * 40),
                  height: 150 + (_pulseController.value * 40),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: const Color(
                      0xFFFFB300,
                    ).withValues(alpha: 0.2), // Light amber
                  ),
                ),
                // Inner solid core
                Container(
                  width: 100,
                  height: 100,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    color: Color(0xFFFF8F00), // Deep amber
                    boxShadow: [
                      BoxShadow(
                        color: Color(0xFFFF8F00),
                        blurRadius: 20,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                  child: const Icon(Icons.mic, size: 40, color: Colors.white),
                ),
              ],
            );
          },
        );

      case 'transcribing':
        return RotationTransition(
          turns: _spinController,
          child: Stack(
            alignment: Alignment.center,
            children: [
              // Spinning dashed ring
              SizedBox(
                width: 130,
                height: 130,
                child: CircularProgressIndicator(
                  strokeWidth: 4,
                  valueColor: const AlwaysStoppedAnimation<Color>(
                    Color(0xFFFF8F00),
                  ),
                  backgroundColor: Colors.white.withValues(alpha: 0.3),
                ),
              ),
              // Pulsing core
              AnimatedBuilder(
                animation: _pulseController,
                builder: (context, child) {
                  return Container(
                    width: 90 - (_pulseController.value * 10),
                    height: 90 - (_pulseController.value * 10),
                    decoration: const BoxDecoration(
                      shape: BoxShape.circle,
                      color: Color(0xFFFFB300),
                    ),
                  );
                },
              ),
            ],
          ),
        );

      default:
        // Idle state
        return GestureDetector(
          onTap: _triggerMicRemotely,
          child: Container(
            width: 100,
            height: 100,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: Colors.white.withValues(alpha: 0.6),
              border: Border.all(
                color: const Color(0xFFFFB300).withValues(alpha: 0.5),
                width: 2,
              ),
            ),
            child: const Icon(
              Icons.graphic_eq,
              size: 40,
              color: Color(0xFFFF8F00),
            ),
          ),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        // The Banana Yellow Gradient Background
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Color(0xFFFFFDE7), // Very light creamy yellow
              Color(0xFFFFF59D), // Banana yellow
            ],
          ),
        ),
        child: Stack(
          children: [
            Positioned.fill(
              child: IgnorePointer(
                child: Container(
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: const Color(0xFFFF8F00).withValues(alpha: 1.0),
                      width: 14,
                    ),
                  ),
                ),
              ),
            ),
            // --- NEW TOP-RIGHT PATTERN ---
            Positioned(
              top: 0,
              right: 0,
              child: Opacity(
                opacity: 1.0,
                child: Image.asset(
                  'assets/rightBorder.png',
                  width: 250,
                  height: 250,
                  fit: BoxFit.contain,
                  color: const Color(0xFFFF8F00),
                  colorBlendMode: BlendMode.srcIn,
                ),
              ),
            ),
            Positioned(
              top: 0,
              left: 0,
              child: Opacity(
                opacity: 0.8,
                child: Image.asset(
                  'assets/leftBorder.png',
                  width: 250,
                  height: 250,
                  fit: BoxFit.contain,
                  color: const Color(0xFFFF8F00),
                  colorBlendMode: BlendMode.srcIn,
                ),
              ),
            ),
            Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 40.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Header
                    const Text(
                      'CHITRA',
                      style: TextStyle(
                        fontSize: 50,
                        fontFamily: 'Samarkan', // Uses your new custom font
                        letterSpacing: 4,
                        color: Color(0xFF424242),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _status.toUpperCase(),
                      style: const TextStyle(
                        fontSize: 13,
                        letterSpacing: 4,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFFFF8F00),
                      ),
                    ),

                    const SizedBox(height: 80),

                    // The Central Animated Agent
                    SizedBox(height: 200, child: _buildAgentCore()),

                    const SizedBox(height: 60),

                    // Frosted Glass Text Output Box
                    ClipRRect(
                      borderRadius: BorderRadius.circular(24),
                      child: BackdropFilter(
                        filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
                        child: Container(
                          width: 600,
                          padding: const EdgeInsets.all(30),
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(
                              alpha: 0.6,
                            ), // Translucent white card
                            borderRadius: BorderRadius.circular(24),
                            border: Border.all(
                              color: Colors.white.withValues(alpha: 0.8),
                              width: 1.5,
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withValues(alpha: 0.05),
                                blurRadius: 20,
                                offset: const Offset(0, 10),
                              ),
                            ],
                          ),
                          child: Text(
                            _message,
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              fontSize: 20,
                              height: 1.5,
                              fontWeight: FontWeight.w500,
                              color: Color(0xFF37474F), // Deep blue-grey text
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
