import 'package:flutter/material.dart';

class HealthIndicator extends StatelessWidget {
  final int health;

  const HealthIndicator({super.key, required this.health});

  Color getColor() {
    if (health >= 80) return Colors.green;
    if (health >= 60) return Colors.orange;
    return Colors.red;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: getColor().withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: getColor()),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            health >= 80 ? Icons.health_and_safety : Icons.warning,
            color: getColor(),
            size: 16,
          ),
          const SizedBox(width: 5),
          Text(
            '$health%',
            style: TextStyle(color: getColor(), fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}
