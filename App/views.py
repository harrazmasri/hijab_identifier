import os
import numpy as np
import onnxruntime as ort
from PIL import Image
from django.shortcuts import render
from App.forms import ImageMediaForm
from App.models import ImageMedia
from django.conf import settings

def preprocess_image(image_path):
    image = Image.open(image_path).convert('RGB')

    w, h = image.size
    min_dim = min(w, h)
    new_w = int(w * 256 / min_dim)
    new_h = int(h * 256 / min_dim)
    image = image.resize((new_w, new_h), Image.Resampling.BILINEAR)

    left = int(round((new_w - 224) / 2.0))
    top = int(round((new_h - 224) / 2.0))
    image = image.crop((left, top, left + 224, top + 224))

    img_data = np.array(image, dtype=np.float32) / 255.0

    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img_data = (img_data - mean) / std

    img_data = np.transpose(img_data, (2, 0, 1))
    img_data = np.expand_dims(img_data, axis=0)

    return img_data

def make_prediction (image_path):
    if not os.path.exists(image_path):
        print(f"Error: File '{image_path}' not found. Try again.")
        return

    model_path = settings.BASE_DIR / 'src/model/hijab_resnet_model.onnx'
    
    ort_session = ort.InferenceSession(str(model_path))

    input_tensor = preprocess_image(image_path)
    input_name = ort_session.get_inputs()[0].name

    outputs = ort_session.run(None, {input_name: input_tensor})

    logit = outputs[0][0][0]
    prob_nonhijab = 1 / (1 + np.exp(-logit))
    prob_hijab = 1 - prob_nonhijab

    # Determine class
    if prob_nonhijab >= 0.5:
        predicted_index = 1
        predicted_class_name = 'nonhijab'
        confidence = prob_nonhijab
    else:
        predicted_index = 0
        predicted_class_name = 'hijab'
        confidence = prob_hijab

    print(f"Predicted: {predicted_class_name} with {confidence:.4f} confidence")

    relative_path = os.path.relpath(image_path, settings.MEDIA_ROOT)
    media_url = settings.MEDIA_URL + relative_path.replace(os.sep, '/')

    return {
        'path': media_url,
        'probability': f"{confidence:.4f}",
        'raw_logit': f"{logit:.4f}",
        'predicted_class': predicted_class_name,
        'is_hijab': predicted_index == 0,
    }

def index (request):
    try:
        image_path = ""
        prediction_data = None

        if (request.method == 'POST'):
            f = request.FILES.get('file')
            filename = f.name if f else ''
            extension = os.path.splitext(filename)[1].lstrip('.') if f else ''

            form = ImageMediaForm(
                data = {
                    'filename': filename,
                    'extension': extension,
                },
                files = request.FILES
            )

            if form.is_valid():
                instance = form.save()

                if hasattr(instance, 'file') and instance.file:
                    image_path = instance.file.path
                    print()
                else:
                    image_path = instance.path
            
            if image_path:
                prediction_data = make_prediction(image_path)

            newest_id = ImageMedia.objects.latest('id').id
            duplicates = ImageMedia.objects.exclude(id=newest_id)

            deleted_count = 0
            
            for obj in duplicates:
                if obj.file and hasattr(obj.file, 'path') and os.path.exists(obj.file.path):
                    os.remove(obj.file.path)
                
                obj.delete()
                deleted_count += 1
                
        return render(request, 'hijab_identifier/index.html', {'payload': prediction_data})

    except Exception as e:
        print(f"Error: {e}")
        return render(request, 'hijab_identifier/index.html', {'error': str(e)})
