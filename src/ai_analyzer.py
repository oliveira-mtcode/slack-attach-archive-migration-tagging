"""AI analysis module using Google Cloud Vision and Video Intelligence APIs."""

import os
from typing import List, Dict, Any, Optional
from google.cloud import vision
from google.cloud import videointelligence
from google.cloud import storage
from src.logger import MigrationLogger
from src.config import Config

class AIAnalyzer:
    """AI-powered file analysis using Google Cloud APIs."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = MigrationLogger("ai_analyzer")
        self.vision_client = vision.ImageAnnotatorClient()
        self.video_client = videointelligence.VideoIntelligenceServiceClient()
        self.storage_client = storage.Client()
    
    def analyze_image(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze an image using Google Cloud Vision API."""
        try:
            with open(file_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Configure features based on config
            features = []
            for feature_name in self.config.vision_features:
                features.append(getattr(vision.Feature.Type, feature_name))
            
            response = self.vision_client.annotate_image({
                'image': image,
                'features': [{'type': feature} for feature in features],
                'max_results': self.config.get('google.vision.max_results', 10)
            })
            
            tags = []
            
            # Process different types of annotations
            if response.label_annotations:
                for label in response.label_annotations:
                    tags.append({
                        'type': 'label',
                        'description': label.description,
                        'confidence': label.score,
                        'source': 'vision_api'
                    })
            
            if response.text_annotations:
                for text in response.text_annotations:
                    tags.append({
                        'type': 'text',
                        'description': text.description,
                        'confidence': text.confidence if hasattr(text, 'confidence') else 1.0,
                        'source': 'vision_api'
                    })
            
            if response.face_annotations:
                for face in response.face_annotations:
                    tags.append({
                        'type': 'face',
                        'description': f"Face detected (joy: {face.joy_likelihood}, sorrow: {face.sorrow_likelihood})",
                        'confidence': 1.0,
                        'source': 'vision_api'
                    })
            
            if response.landmark_annotations:
                for landmark in response.landmark_annotations:
                    tags.append({
                        'type': 'landmark',
                        'description': landmark.description,
                        'confidence': landmark.score,
                        'source': 'vision_api'
                    })
            
            if response.logo_annotations:
                for logo in response.logo_annotations:
                    tags.append({
                        'type': 'logo',
                        'description': logo.description,
                        'confidence': logo.score,
                        'source': 'vision_api'
                    })
            
            if response.web_detection:
                web = response.web_detection
                if web.web_entities:
                    for entity in web.web_entities:
                        tags.append({
                            'type': 'web_entity',
                            'description': entity.description,
                            'confidence': entity.score,
                            'source': 'vision_api'
                        })
            
            self.logger.info(f"Analyzed image: {file_path}", 
                           tags_count=len(tags))
            return tags
            
        except Exception as e:
            self.logger.log_error_with_context(e, {
                "operation": "analyze_image",
                "file_path": file_path
            })
            return []
    
    def analyze_video(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze a video using Google Cloud Video Intelligence API."""
        try:
            # Upload file to Cloud Storage for analysis
            bucket_name = f"{self.config.google_project_id}-video-analysis"
            blob_name = os.path.basename(file_path)
            
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(file_path)
            
            gcs_uri = f"gs://{bucket_name}/{blob_name}"
            
            # Configure features
            features = []
            for feature_name in self.config.video_intelligence_features:
                features.append(getattr(videointelligence.Feature, feature_name))
            
            # Start analysis
            operation = self.video_client.annotate_video(
                request={
                    "input_uri": gcs_uri,
                    "features": features,
                }
            )
            
            # Wait for completion
            result = operation.result(timeout=300)  # 5 minutes timeout
            
            tags = []
            
            # Process label annotations
            if result.annotation_results:
                for annotation_result in result.annotation_results:
                    if annotation_result.segment_label_annotations:
                        for segment_label in annotation_result.segment_label_annotations:
                            for entity in segment_label.entities:
                                tags.append({
                                    'type': 'video_label',
                                    'description': entity.description,
                                    'confidence': entity.confidence,
                                    'source': 'video_intelligence_api',
                                    'segment_start': segment_label.segment.start_time_offset.total_seconds(),
                                    'segment_end': segment_label.segment.end_time_offset.total_seconds()
                                })
                    
                    if annotation_result.shot_label_annotations:
                        for shot_label in annotation_result.shot_label_annotations:
                            for entity in shot_label.entities:
                                tags.append({
                                    'type': 'shot_label',
                                    'description': entity.description,
                                    'confidence': entity.confidence,
                                    'source': 'video_intelligence_api'
                                })
                    
                    if annotation_result.text_annotations:
                        for text_annotation in annotation_result.text_annotations:
                            tags.append({
                                'type': 'video_text',
                                'description': text_annotation.text,
                                'confidence': 1.0,
                                'source': 'video_intelligence_api'
                            })
            
            # Clean up uploaded file
            blob.delete()
            
            self.logger.info(f"Analyzed video: {file_path}", 
                           tags_count=len(tags))
            return tags
            
        except Exception as e:
            self.logger.log_error_with_context(e, {
                "operation": "analyze_video",
                "file_path": file_path
            })
            return []
    
    def generate_file_description(self, tags: List[Dict[str, Any]], 
                                file_type: str) -> str:
        """Generate a human-readable description from tags."""
        if not tags:
            return f"Uploaded {file_type} file"
        
        # Group tags by type
        tag_groups = {}
        for tag in tags:
            tag_type = tag.get('type', 'unknown')
            if tag_type not in tag_groups:
                tag_groups[tag_type] = []
            tag_groups[tag_type].append(tag)
        
        description_parts = []
        
        # Add high-confidence labels
        if 'label' in tag_groups:
            high_conf_labels = [
                tag['description'] for tag in tag_groups['label'] 
                if tag.get('confidence', 0) > 0.7
            ]
            if high_conf_labels:
                description_parts.append(f"Contains: {', '.join(high_conf_labels[:5])}")
        
        # Add text content
        if 'text' in tag_groups:
            text_content = [tag['description'] for tag in tag_groups['text']]
            if text_content:
                description_parts.append(f"Text: {text_content[0][:100]}...")
        
        # Add special features
        special_features = []
        for feature_type in ['face', 'landmark', 'logo']:
            if feature_type in tag_groups:
                special_features.append(feature_type)
        
        if special_features:
            description_parts.append(f"Features: {', '.join(special_features)}")
        
        return " | ".join(description_parts) if description_parts else f"Uploaded {file_type} file"

# tweak 16 at 2025-09-26 19:30:07
