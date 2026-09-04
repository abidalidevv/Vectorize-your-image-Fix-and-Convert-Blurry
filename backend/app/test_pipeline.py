"""Quick pipeline test"""
import sys
sys.path.insert(0, '.')
from pathlib import Path
from image_processing.analyzer import analyze_image
from image_processing.quantizer import quantize_image
from vectorization.vtracer_engine import VTracerEngine
from utils.svg_optimizer import validate_svg

sample = Path('../../samples/test_logo.png')
print('=== ANALYSIS TEST ===')
result = analyze_image(sample)
print('Recommended mode:', result['recommended_mode'])
print('Confidence:', round(result['confidence']*100), '%')
print('Colors estimate:', result['color_count_estimate'])
print('Grayscale:', result['is_grayscale'])

print()
print('=== QUANTIZE TEST ===')
out = Path('../../samples/test_quantized.png')
q = quantize_image(sample, out, num_colors=8, method='kmeans')
print('Palette colors:', len(q['palette']))
print('Top colors:', [c['hex'] for c in q['palette'][:5]])

print()
print('=== VECTORIZE TEST ===')
engine = VTracerEngine()
svg_out = Path('../../samples/test_vector.svg')
vresult = engine.trace(out, svg_out, {'quality_preset': 'balanced'})
print('Success:', vresult['success'])
if not vresult['success']:
    print('Error:', vresult['error'])
else:
    print('SVG size:', vresult['svg_size'], 'bytes')
    svg_content = svg_out.read_text()
    path_count = svg_content.count('<path ')
    has_viewbox = 'viewBox' in svg_content
    has_raster = '<image' in svg_content
    print('Path elements:', path_count)
    print('Has viewBox:', has_viewbox)
    print('Has embedded raster:', has_raster)

    validation = validate_svg(svg_content)
    print()
    print('=== SVG VALIDATION ===')
    print('Valid:', validation['valid'])
    stats = validation['stats']
    print('Paths:', stats['path_count'])
    print('Groups:', stats['group_count'])
    print('Colors:', stats['color_count'])
    print('Contains raster:', stats['contains_raster'])
    if validation['errors']:
        print('Errors:', validation['errors'])
    else:
        print('No errors - pure vector SVG!')
