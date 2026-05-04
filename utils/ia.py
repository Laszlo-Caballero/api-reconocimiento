import torch
import clip
from decorator.singleton import singleton

@singleton
class IA:
    device: str
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
    
    def to_vector_image(self, image):
        image = self.preprocess(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            image_features = self.model.encode_image(image)
            return image_features.cpu().numpy()[0]
    