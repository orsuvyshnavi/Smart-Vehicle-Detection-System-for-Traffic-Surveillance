import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict, Counter
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

# Set style for matplotlib
plt.style.use('dark_background')
sns.set_palette("husl")

class VehicleDetectionAnalyzer:
    def __init__(self):
        self.data = {
            'timestamp': [],
            'vehicle_type': [],
            'confidence': [],
            'weather_condition': [],
            'processing_time': [],
            'fps': [],
            'bbox_area': []
        }
        self.weather_conditions = ['normal', 'rain', 'fog', 'night', 'snow']
        self.vehicle_types = ['car', 'truck', 'bus', 'motorcycle', 'bicycle', 'person']
        self.simulation_data = self.generate_simulation_data()
    
    def generate_simulation_data(self, num_samples=1000):
        """Generate realistic simulation data for demonstration"""
        np.random.seed(42)
        
        # Time series data
        base_time = datetime.now() - timedelta(hours=2)
        timestamps = [base_time + timedelta(seconds=i*7.2) for i in range(num_samples)]
        
        # Vehicle type distribution (cars are most common)
        vehicle_weights = [0.6, 0.15, 0.1, 0.08, 0.05, 0.02]  # car, truck, bus, motorcycle, bicycle, person
        vehicle_types = np.random.choice(self.vehicle_types, num_samples, p=vehicle_weights)
        
        # Confidence scores (higher for clearer conditions)
        confidence_scores = np.random.beta(8, 2, num_samples) * 0.3 + 0.7  # High confidence (0.7-1.0)
        
        # Weather conditions
        weather_weights = [0.5, 0.2, 0.15, 0.1, 0.05]  # normal, rain, fog, night, snow
        weather_conditions = np.random.choice(self.weather_conditions, num_samples, p=weather_weights)
        
        # Processing time (affected by weather and vehicle complexity)
        base_processing_time = 0.015  # 15ms base
        weather_multiplier = {'normal': 1.0, 'rain': 1.2, 'fog': 1.3, 'night': 1.1, 'snow': 1.4}
        processing_times = []
        
        for i, weather in enumerate(weather_conditions):
            multiplier = weather_multiplier[weather]
            # Larger vehicles take slightly longer to process
            vehicle_multiplier = 1.0 if vehicle_types[i] in ['car', 'motorcycle'] else 1.1
            processing_time = base_processing_time * multiplier * vehicle_multiplier
            processing_time += np.random.normal(0, 0.002)  # Add some noise
            processing_times.append(max(0.005, processing_time))  # Minimum 5ms
        
        # FPS calculation
        fps_scores = [1.0 / pt for pt in processing_times]
        
        # Bounding box areas (normalized)
        bbox_areas = np.random.uniform(0.05, 0.3, num_samples)
        
        return {
            'timestamps': timestamps,
            'vehicle_types': vehicle_types,
            'confidence_scores': confidence_scores,
            'weather_conditions': weather_conditions,
            'processing_times': processing_times,
            'fps_scores': fps_scores,
            'bbox_areas': bbox_areas
        }
    
    def create_performance_analysis(self):
        """Create comprehensive performance analysis charts"""
        data = self.simulation_data
        
        # Performance Metrics Over Time
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('FPS Performance', 'Processing Time', 'Confidence Distribution', 'Weather Impact'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # FPS over time
        fig.add_trace(
            go.Scatter(x=data['timestamps'][::50], y=data['fps_scores'][::50],
                      mode='lines+markers', name='FPS',
                      line=dict(color='#10B981', width=2)),
            row=1, col=1
        )
        
        # Processing time over time
        fig.add_trace(
            go.Scatter(x=data['timestamps'][::50], 
                      y=[pt*1000 for pt in data['processing_times'][::50]],
                      mode='lines+markers', name='Processing Time (ms)',
                      line=dict(color='#F59E0B', width=2)),
            row=1, col=2
        )
        
        # Confidence distribution
        fig.add_trace(
            go.Histogram(x=data['confidence_scores'], nbinsx=20,
                        name='Confidence', marker_color='#3B82F6'),
            row=2, col=1
        )
        
        # Weather impact
        weather_data = Counter(data['weather_conditions'])
        fig.add_trace(
            go.Bar(x=list(weather_data.keys()), y=list(weather_data.values()),
                   name='Weather Count', marker_color='#8B5CF6'),
            row=2, col=2
        )
        
        fig.update_layout(
            title_text="Vehicle Detection Performance Analysis",
            title_x=0.5,
            height=800,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        # Update axes
        fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)', color='white')
        fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)', color='white')
        
        return fig
    
    def create_vehicle_type_analysis(self):
        """Analyze vehicle type distribution and patterns"""
        data = self.simulation_data
        
        # Vehicle type distribution
        vehicle_counts = Counter(data['vehicle_types'])
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Vehicle Type Distribution', 'Weather vs Vehicle Type'),
            specs=[[{"type": "pie"}, {"type": "heatmap"}]]
        )
        
        # Pie chart
        fig.add_trace(
            go.Pie(labels=list(vehicle_counts.keys()), 
                   values=list(vehicle_counts.values()),
                   hole=0.4,
                   marker_colors=['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#F97316']),
            row=1, col=1
        )
        
        # Heatmap: Weather vs Vehicle Type
        weather_vehicle_matrix = np.zeros((len(self.weather_conditions), len(self.vehicle_types)))
        for i, weather in enumerate(self.weather_conditions):
            for j, vehicle in enumerate(self.vehicle_types):
                mask = (np.array(data['weather_conditions']) == weather) & (np.array(data['vehicle_types']) == vehicle)
                weather_vehicle_matrix[i, j] = np.sum(mask)
        
        fig.add_trace(
            go.Heatmap(z=weather_vehicle_matrix,
                      x=self.vehicle_types,
                      y=self.weather_conditions,
                      colorscale='Viridis',
                      showscale=True),
            row=1, col=2
        )
        
        fig.update_layout(
            title_text="Vehicle Type Analysis",
            title_x=0.5,
            height=500,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        return fig
    
    def create_robustness_analysis(self):
        """Analyze system robustness across different conditions"""
        data = self.simulation_data
        
        # Calculate performance metrics by weather condition
        weather_stats = {}
        for weather in self.weather_conditions:
            mask = np.array(data['weather_conditions']) == weather
            if np.sum(mask) > 0:
                weather_stats[weather] = {
                    'avg_fps': np.mean(np.array(data['fps_scores'])[mask]),
                    'avg_processing_time': np.mean(np.array(data['processing_times'])[mask]),
                    'avg_confidence': np.mean(np.array(data['confidence_scores'])[mask]),
                    'count': np.sum(mask)
                }
        
        # Create comparison chart
        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=('FPS by Weather', 'Processing Time by Weather', 'Confidence by Weather')
        )
        
        weathers = list(weather_stats.keys())
        fps_values = [weather_stats[w]['avg_fps'] for w in weathers]
        time_values = [weather_stats[w]['avg_processing_time'] * 1000 for w in weathers]  # Convert to ms
        conf_values = [weather_stats[w]['avg_confidence'] for w in weathers]
        
        fig.add_trace(
            go.Bar(x=weathers, y=fps_values, name='FPS', marker_color='#10B981'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(x=weathers, y=time_values, name='Processing Time (ms)', marker_color='#F59E0B'),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Bar(x=weathers, y=conf_values, name='Confidence', marker_color='#3B82F6'),
            row=1, col=3
        )
        
        fig.update_layout(
            title_text="System Robustness Analysis",
            title_x=0.5,
            height=400,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)', color='white')
        fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)', color='white')
        
        return fig
    
    def save_analysis_results(self):
        """Save all analysis results to files"""
        # Create output directory
        os.makedirs('analysis_results', exist_ok=True)
        
        # Performance analysis
        perf_fig = self.create_performance_analysis()
        perf_fig.write_html('analysis_results/performance_analysis.html')
        
        # Vehicle type analysis
        vehicle_fig = self.create_vehicle_type_analysis()
        vehicle_fig.write_html('analysis_results/vehicle_type_analysis.html')
        
        # Robustness analysis
        robust_fig = self.create_robustness_analysis()
        robust_fig.write_html('analysis_results/robustness_analysis.html')
        
        # Save raw data as CSV
        df = pd.DataFrame({
            'timestamp': self.simulation_data['timestamps'],
            'vehicle_type': self.simulation_data['vehicle_types'],
            'confidence': self.simulation_data['confidence_scores'],
            'weather_condition': self.simulation_data['weather_conditions'],
            'processing_time_ms': [pt * 1000 for pt in self.simulation_data['processing_times']],
            'fps': self.simulation_data['fps_scores'],
            'bbox_area': self.simulation_data['bbox_areas']
        })
        df.to_csv('analysis_results/vehicle_detection_data.csv', index=False)
        
        # Save summary statistics
        summary_stats = {
            'total_detections': len(self.simulation_data['timestamps']),
            'vehicle_distribution': dict(Counter(self.simulation_data['vehicle_types'])),
            'weather_distribution': dict(Counter(self.simulation_data['weather_conditions'])),
            'performance_metrics': {
                'avg_fps': np.mean(self.simulation_data['fps_scores']),
                'avg_processing_time_ms': np.mean(self.simulation_data['processing_times']) * 1000,
                'avg_confidence': np.mean(self.simulation_data['confidence_scores']),
                'min_fps': np.min(self.simulation_data['fps_scores']),
                'max_fps': np.max(self.simulation_data['fps_scores']),
                'std_fps': np.std(self.simulation_data['fps_scores'])
            },
            'weather_impact': {}
        }
        
        # Calculate weather-specific metrics
        for weather in self.weather_conditions:
            mask = np.array(self.simulation_data['weather_conditions']) == weather
            if np.sum(mask) > 0:
                summary_stats['weather_impact'][weather] = {
                    'count': int(np.sum(mask)),
                    'avg_fps': float(np.mean(np.array(self.simulation_data['fps_scores'])[mask])),
                    'avg_processing_time_ms': float(np.mean(np.array(self.simulation_data['processing_times'])[mask]) * 1000),
                    'avg_confidence': float(np.mean(np.array(self.simulation_data['confidence_scores'])[mask]))
                }
        
        with open('analysis_results/summary_statistics.json', 'w') as f:
            json.dump(summary_stats, f, indent=2, default=str)
        
        print("Analysis results saved to 'analysis_results/' directory")
        return summary_stats

def main():
    """Main analysis function"""
    print("Starting Vehicle Detection Analysis...")
    
    # Initialize analyzer
    analyzer = VehicleDetectionAnalyzer()
    
    # Generate and save analysis
    results = analyzer.save_analysis_results()
    
    # Print summary
    print("\n=== ANALYSIS SUMMARY ===")
    print(f"Total Detections: {results['total_detections']}")
    print(f"Average FPS: {results['performance_metrics']['avg_fps']:.2f}")
    print(f"Average Processing Time: {results['performance_metrics']['avg_processing_time_ms']:.2f}ms")
    print(f"Average Confidence: {results['performance_metrics']['avg_confidence']:.3f}")
    print("\nVehicle Distribution:")
    for vehicle, count in results['vehicle_distribution'].items():
        print(f"  {vehicle}: {count}")
    print("\nWeather Impact:")
    for weather, stats in results['weather_impact'].items():
        print(f"  {weather}: {stats['count']} detections, {stats['avg_fps']:.2f} FPS")
    
    return analyzer

if __name__ == "__main__":
    analyzer = main()