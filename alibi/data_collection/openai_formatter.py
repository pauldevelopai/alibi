"""
OpenAI Fine-Tuning Format Converter
Converts collected training data to OpenAI's fine-tuning format
"""
import json
import base64
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image
from io import BytesIO


class OpenAIFormatter:
    """Converts training data to OpenAI fine-tuning format"""
    
    def __init__(self, collected_data_file: Path):
        self.collected_data_file = collected_data_file
    
    def convert_to_openai_format(self, output_file: Path, include_images: bool = False) -> Dict:
        """
        Convert collected data to OpenAI fine-tuning format
        
        OpenAI Vision fine-tuning format:
        {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a security camera AI assistant..."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this security camera image"},
                        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
                    ]
                },
                {
                    "role": "assistant",
                    "content": "Description of what's in the image..."
                }
            ]
        }
        """
        print(f"📝 Converting {self.collected_data_file} to OpenAI format...")
        
        if not self.collected_data_file.exists():
            return {"success": False, "error": "Collected data file not found"}
        
        # Load collected examples
        examples = []
        with open(self.collected_data_file, 'r') as f:
            for line in f:
                try:
                    examples.append(json.loads(line))
                except:
                    continue
        
        print(f"   Found {len(examples)} examples to convert")
        
        # Convert each example
        converted = []
        skipped = 0
        
        for i, example in enumerate(examples):
            try:
                openai_example = self._convert_example(example, include_images)
                if openai_example:
                    converted.append(openai_example)
                else:
                    skipped += 1
                
                if (i + 1) % 50 == 0:
                    print(f"   Converted {i + 1}/{len(examples)} examples...")
            
            except Exception as e:
                print(f"   ⚠️ Error converting example {i}: {e}")
                skipped += 1
                continue
        
        # Save to output file
        with open(output_file, 'w') as f:
            for example in converted:
                f.write(json.dumps(example) + '\n')
        
        print(f"✅ Conversion complete!")
        print(f"   Converted: {len(converted)} examples")
        print(f"   Skipped: {skipped} examples")
        print(f"   Output: {output_file}")
        
        return {
            "success": True,
            "converted_count": len(converted),
            "skipped_count": skipped,
            "output_file": str(output_file)
        }
    
    def _convert_example(self, example: Dict, include_images: bool) -> Optional[Dict]:
        """Convert a single example to OpenAI format"""
        
        # Get image path
        image_path = example.get('image_path')
        if not image_path or not Path(image_path).exists():
            return None
        
        # Load and encode image if needed
        image_content = None
        if include_images:
            try:
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                    image_content = f"data:image/jpeg;base64,{image_b64}"
            except Exception as e:
                print(f"   ⚠️ Error encoding image: {e}")
                return None
        else:
            # Use file path reference
            image_content = f"file://{image_path}"
        
        # Build security-focused system message
        system_message = self._build_system_message(example.get('category', 'baseline'))
        
        # Build user prompt based on category
        user_prompt = self._build_user_prompt(example.get('category', 'baseline'))
        
        # Get assistant response (the description)
        assistant_response = example.get('description', '')
        if example.get('security_relevance'):
            assistant_response += f"\n\nSecurity Relevance: {example['security_relevance']}"
        
        # Build OpenAI format
        openai_example = {
            "messages": [
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": image_content}}
                    ]
                },
                {
                    "role": "assistant",
                    "content": assistant_response
                }
            ]
        }
        
        return openai_example
    
    def _build_system_message(self, category: str) -> str:
        """Build category-specific system message"""
        base = "You are a security camera AI assistant analyzing surveillance footage. "
        
        category_specific = {
            "person": "Focus on identifying people, their actions, and potential security concerns.",
            "vehicle": "Focus on identifying vehicles, their types, colors, and license plates when visible.",
            "suspicious_object": "Focus on identifying potentially dangerous objects and security threats.",
            "crowd": "Focus on crowd density, behavior patterns, and potential safety concerns.",
            "activity": "Focus on identifying activities and behaviors that may require security attention.",
            "baseline": "Provide clear, accurate descriptions of all objects and activities in the scene."
        }
        
        return base + category_specific.get(category, category_specific["baseline"])
    
    def _build_user_prompt(self, category: str) -> str:
        """Build category-specific user prompt"""
        prompts = {
            "person": "Analyze this security camera image. Describe any people visible, their actions, and note any security concerns.",
            "vehicle": "Analyze this security camera image. Describe any vehicles visible, their types, colors, and positions.",
            "suspicious_object": "Analyze this security camera image. Identify any objects that may pose security concerns.",
            "crowd": "Analyze this security camera image. Describe the crowd density, behavior, and any safety concerns.",
            "activity": "Analyze this security camera image. Describe the activities and behaviors occurring.",
            "baseline": "Analyze this security camera image. Provide a detailed description of what you see."
        }
        
        return prompts.get(category, prompts["baseline"])


def convert_collected_data_to_openai(
    input_file: str = "alibi/data/hf_training_data/collected_examples.jsonl",
    output_file: str = "alibi/data/hf_training_data/openai_training_dataset.jsonl",
    include_images: bool = False
) -> Dict:
    """
    Convert collected training data to OpenAI format
    
    Args:
        input_file: Path to collected examples
        output_file: Where to save OpenAI format data
        include_images: Whether to embed images as base64 (slower but portable)
    
    Returns:
        Dict with conversion results
    """
    formatter = OpenAIFormatter(Path(input_file))
    return formatter.convert_to_openai_format(Path(output_file), include_images)


if __name__ == "__main__":
    # Test conversion
    result = convert_collected_data_to_openai()
    print(f"\n✅ Conversion result: {result}")
