import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';
import 'dart:ui';
import 'dart:math' as math;

void main() {
  runApp(const ShrutiApp());
}

class ShrutiApp extends StatelessWidget {
  const ShrutiApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Shruti Voice Assistant',
      theme: ThemeData.light().copyWith(
        primaryColor: const Color(0xFFFFB300), // Amber accent
      ),
      home: const SplashScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

// ==========================================
// 1. THE SPLASH SCREEN WIDGET (Theatrical Curtains)
// ==========================================
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _curtainController;
  late Animation<double> _curtainProgress;

  @override
  void initState() {
    super.initState();

    _curtainController = AnimationController(
      vsync: this,
      duration: const Duration(
        milliseconds: 1500,
      ), // Slightly slower for dramatic effect
    );

    // This single value tracks the "openness" of the curtain from 0.0 to 1.0
    _curtainProgress = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _curtainController, curve: Curves.easeInOutCubic),
    );

    _startSequence();
  }

  void _startSequence() async {
    await Future.delayed(const Duration(milliseconds: 600));
    if (!mounted) return;

    await _curtainController.forward();

    await Future.delayed(const Duration(seconds: 1));
    if (!mounted) return;

    Navigator.pushReplacement(
      context,
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) =>
            FadeTransition(opacity: animation, child: const ShrutiHomeScreen()),
        transitionDuration: const Duration(milliseconds: 600),
      ),
    );
  }

  @override
  void dispose() {
    _curtainController.dispose();
    super.dispose();
  }

  Widget _buildCurtainPanel(bool isLeft, Size size) {
    // A complex gradient to simulate deep red velvet folds
    const curtainGradient = LinearGradient(
      colors: [
        Color(0xFF5D0000), // Deep shadow
        Color(0xFFD32F2F), // Highlight
        Color(0xFF7F0000), // Shadow
        Color(0xFFE53935), // Highlight
        Color(0xFF5D0000), // Deep shadow
      ],
      stops: [0.0, 0.25, 0.5, 0.75, 1.0],
    );

    return AnimatedBuilder(
      animation: _curtainProgress,
      builder: (context, child) {
        // As the curtain opens, we squash its width down to simulate gathering fabric.
        // math.max prevents the scale from hitting exactly 0.0, which can cause rendering errors.
        final scaleX = math.max(0.001, 1.0 - _curtainProgress.value);

        return Transform(
          alignment: isLeft ? Alignment.centerLeft : Alignment.centerRight,
          // ignore: deprecated_member_use
          transform: Matrix4.identity()..scale(scaleX, 1.0),
          child: ClipPath(
            clipper: CurtainClipper(
              progress: _curtainProgress.value,
              isLeft: isLeft,
            ),
            child: Container(
              width: size.width / 2,
              height: size.height,
              decoration: const BoxDecoration(
                gradient: curtainGradient,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black87,
                    blurRadius: 20,
                    spreadRadius: 5,
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;

    return Scaffold(
      body: Stack(
        children: [
          // LAYER 1: The App UI hiding behind the curtains
          Container(
            width: size.width,
            height: size.height,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFFFFE082), Color(0xFFFF8F00)],
              ),
            ),
            child: Center(
              child: Stack(
                children: [
                  Image.asset(
                    'assets/welcome_border.png',
                    width: double.infinity,
                    height: double.infinity,
                    fit: BoxFit.fitHeight,
                  ),
                  Center(
                    child: Column(
                      children: [
                        const SizedBox(height: 200, width: 50),
                        Image.asset(
                          'assets/welcoming_woman.png',
                          width: 500,
                          height: 300,
                          fit: BoxFit.contain,
                        ),
                        const SizedBox(height: 24),
                        const Text(
                          'SHRUTI',
                          style: TextStyle(
                            fontSize: 50,
                            fontFamily: 'Samarkan',
                            letterSpacing: 4,
                            color: Colors.white,
                            shadows: [
                              Shadow(
                                color: Colors.black26,
                                blurRadius: 10,
                                offset: Offset(0, 4),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 5),
                        Text(
                          'At Your Service.',
                          style: GoogleFonts.inter(
                            textStyle: const TextStyle(
                              fontSize: 24,
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          // LAYER 2: Left Gathered Curtain
          Align(
            alignment: Alignment.centerLeft,
            child: _buildCurtainPanel(true, size),
          ),

          // LAYER 3: Right Gathered Curtain
          Align(
            alignment: Alignment.centerRight,
            child: _buildCurtainPanel(false, size),
          ),
        ],
      ),
    );
  }
}

// ==========================================
// 2. THE CUSTOM FABRIC CLIPPER
// ==========================================
class CurtainClipper extends CustomClipper<Path> {
  final double progress;
  final bool isLeft;

  CurtainClipper({required this.progress, required this.isLeft});

  @override
  Path getClip(Size size) {
    final path = Path();

    if (isLeft) {
      path.moveTo(0, 0); // Anchor to top-left wall
      path.lineTo(0, size.height); // Down to bottom-left floor

      // Control point anchors the swoop to the floor,
      // End point yanks the inner hem upward diagonally.
      path.quadraticBezierTo(
        size.width,
        size.height,
        size.width,
        size.height * (1 - progress),
      );

      path.lineTo(size.width, 0); // Straight up to the ceiling rod
    } else {
      path.moveTo(size.width, 0); // Anchor to top-right wall
      path.lineTo(size.width, size.height); // Down to bottom-right floor

      // Mirror the left side bezier math
      path.quadraticBezierTo(0, size.height, 0, size.height * (1 - progress));

      path.lineTo(0, 0);
    }

    path.close();
    return path;
  }

  @override
  bool shouldReclip(CurtainClipper oldClipper) =>
      progress != oldClipper.progress;
}
//==========================================
// 1. THE HOME SCREEN WIDGET
// ==========================================

class ShrutiHomeScreen extends StatefulWidget {
  const ShrutiHomeScreen({super.key});

  @override
  State<ShrutiHomeScreen> createState() => _ShrutiHomeScreenState();
}

class _ShrutiHomeScreenState extends State<ShrutiHomeScreen>
    with TickerProviderStateMixin {
  late WebSocketChannel _channel;
  String _status = 'idle';
  String _message = 'Namaste. Press Ctrl+Shift+Space to speak.';
  bool _showDraftPanel = false;
  String _draftContent = "";

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
            if (_status == 'draft_review') {
              _showDraftPanel = true;
              _draftContent = data['draft_text'] ?? '';
            } else if (_status == 'success' || _status == 'idle') {
              _showDraftPanel = false;
            }
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

  Widget _buildDraftPanel() {
    return AnimatedPositioned(
      duration: const Duration(milliseconds: 400),
      curve: Curves.easeOutQuart,
      // Slide in from the left, or hide completely off-screen
      left: _showDraftPanel ? 40 : -450,
      top: 80,
      bottom: 80,
      width: 400,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
          child: Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.7),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(
                color: const Color(0xFFFF8F00).withValues(alpha: 0.5),
                width: 2,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.1),
                  blurRadius: 20,
                  offset: const Offset(5, 5),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  "DRAFT REVIEW",
                  style: TextStyle(
                    fontSize: 14,
                    letterSpacing: 2,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFFFF8F00),
                  ),
                ),
                const SizedBox(height: 16),
                Expanded(
                  child: SingleChildScrollView(
                    child: Text(
                      _draftContent,
                      style: const TextStyle(
                        fontSize: 16,
                        height: 1.5,
                        color: Color(0xFF424242),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                // Action Buttons
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () {
                          // Hide panel and tell Python the user wants changes
                          setState(() => _showDraftPanel = false);
                          _channel.sink.add(
                            jsonEncode({"command": "revise_draft"}),
                          );
                          _triggerMicRemotely(); // Auto-open mic to hear changes
                        },
                        style: OutlinedButton.styleFrom(
                          foregroundColor: const Color(0xFFFF8F00),
                          side: const BorderSide(color: Color(0xFFFF8F00)),
                          padding: const EdgeInsets.symmetric(vertical: 16),
                        ),
                        child: const Text("Revise"),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () {
                          // Hide panel and tell Python to send the email
                          setState(() => _showDraftPanel = false);
                          _channel.sink.add(
                            jsonEncode({"command": "approve_draft"}),
                          );
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFFF8F00),
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                        ),
                        child: const Text("Approve & Send"),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
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
                      'SHRUTI',
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
            _buildDraftPanel(),
          ],
        ),
      ),
    );
  }
}
