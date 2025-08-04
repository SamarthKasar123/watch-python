"""
Data processing utilities for watch data analysis and matching
"""

import pandas as pd
import numpy as np
import re
from typing import List, Dict, Any, Tuple
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz
import json

class WatchDataProcessor:
    """Process and analyze scraped watch data"""
    
    def __init__(self, data_file: str = None):
        self.df = None
        if data_file:
            self.load_data(data_file)
    
    def load_data(self, file_path: str):
        """Load watch data from CSV or JSON file"""
        if file_path.endswith('.csv'):
            self.df = pd.read_csv(file_path)
        elif file_path.endswith('.json'):
            self.df = pd.read_json(file_path)
        else:
            raise ValueError("Unsupported file format. Use CSV or JSON.")
        
        print(f"Loaded {len(self.df)} watches from {file_path}")
    
    def clean_data(self):
        """Clean and standardize watch data"""
        if self.df is None:
            return
        
        # Remove duplicates
        initial_count = len(self.df)
        self.df = self.df.drop_duplicates(subset=['url'], keep='first')
        print(f"Removed {initial_count - len(self.df)} duplicates")
        
        # Clean text fields
        text_fields = ['title', 'brand', 'model', 'reference', 'description']
        for field in text_fields:
            if field in self.df.columns:
                self.df[field] = self.df[field].astype(str).str.strip()
                self.df[field] = self.df[field].replace(['nan', 'None', ''], np.nan)
        
        # Standardize brand names
        self.standardize_brands()
        
        # Extract missing references from titles
        self.extract_references()
        
        # Clean price data
        if 'price' in self.df.columns:
            self.df['price'] = pd.to_numeric(self.df['price'], errors='coerce')
            self.df = self.df[self.df['price'] > 0]  # Remove invalid prices
        
        print(f"Data cleaned. {len(self.df)} valid watches remaining.")
    
    def standardize_brands(self):
        """Standardize brand names"""
        brand_mapping = {
            'rolex': 'Rolex',
            'omega': 'Omega',
            'patek philippe': 'Patek Philippe',
            'audemars piguet': 'Audemars Piguet',
            'cartier': 'Cartier',
            'breitling': 'Breitling',
            'tag heuer': 'TAG Heuer',
            'tudor': 'Tudor',
            'iwc': 'IWC',
            'jaeger-lecoultre': 'Jaeger-LeCoultre',
            'vacheron constantin': 'Vacheron Constantin',
            'richard mille': 'Richard Mille'
        }
        
        if 'brand' in self.df.columns:
            # First try exact mapping
            self.df['brand'] = self.df['brand'].str.lower().map(brand_mapping).fillna(self.df['brand'])
            
            # Extract brand from title if missing
            mask = self.df['brand'].isna()
            if mask.any():
                for brand_key, brand_value in brand_mapping.items():
                    title_mask = self.df['title'].str.lower().str.contains(brand_key, na=False)
                    self.df.loc[mask & title_mask, 'brand'] = brand_value
    
    def extract_references(self):
        """Extract watch reference numbers from titles and descriptions"""
        if 'reference' not in self.df.columns:
            self.df['reference'] = ''
        
        # Common reference patterns
        patterns = [
            r'\b(\d{5,6}[A-Z]*)\b',  # 5-6 digit refs
            r'\bRef[:\.\s]*(\w+)',    # Ref: pattern
            r'\bReference[:\.\s]*(\w+)',  # Reference: pattern
            r'\b(116\d{3})\b',        # Rolex 6-digit
            r'\b(126\d{3})\b',        # Rolex new 6-digit
            r'\b(\d{3}\.\d{2}\.\d{2})\b'  # Omega style
        ]
        
        for idx, row in self.df.iterrows():
            if pd.isna(row['reference']) or row['reference'] == '':
                text = f"{row['title']} {row['description']}".lower()
                
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        self.df.at[idx, 'reference'] = match.group(1).upper()
                        break
    
    def generate_statistics(self) -> Dict[str, Any]:
        """Generate comprehensive statistics about the watch data"""
        if self.df is None:
            return {}
        
        stats = {
            'total_watches': len(self.df),
            'brands': {
                'total_brands': self.df['brand'].nunique(),
                'distribution': self.df['brand'].value_counts().to_dict()
            },
            'sites': {
                'total_sites': self.df['site'].nunique(),
                'distribution': self.df['site'].value_counts().to_dict()
            }
        }
        
        # Price statistics
        if 'price' in self.df.columns:
            price_data = self.df['price'].dropna()
            stats['prices'] = {
                'count': len(price_data),
                'mean': float(price_data.mean()),
                'median': float(price_data.median()),
                'min': float(price_data.min()),
                'max': float(price_data.max()),
                'std': float(price_data.std())
            }
        
        # Brand-specific statistics
        brand_stats = {}
        for brand in self.df['brand'].dropna().unique():
            brand_df = self.df[self.df['brand'] == brand]
            brand_prices = brand_df['price'].dropna()
            
            brand_stats[brand] = {
                'count': len(brand_df),
                'avg_price': float(brand_prices.mean()) if len(brand_prices) > 0 else None,
                'price_range': [float(brand_prices.min()), float(brand_prices.max())] if len(brand_prices) > 0 else None
            }
        
        stats['brand_details'] = brand_stats
        
        return stats
    
    def find_similar_watches(self, watch_data: Dict[str, Any], threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Find similar watches based on brand, model, and reference"""
        if self.df is None:
            return []
        
        similar_watches = []
        
        target_brand = watch_data.get('brand', '').lower()
        target_model = watch_data.get('model', '').lower()
        target_ref = watch_data.get('reference', '').lower()
        target_title = watch_data.get('title', '').lower()
        
        for idx, row in self.df.iterrows():
            similarity_score = 0
            match_factors = []
            
            # Brand matching
            if target_brand and str(row['brand']).lower() == target_brand:
                similarity_score += 0.4
                match_factors.append('brand')
            
            # Reference matching
            if target_ref and str(row['reference']).lower() == target_ref:
                similarity_score += 0.4
                match_factors.append('reference')
            
            # Model matching
            if target_model and target_model in str(row['model']).lower():
                similarity_score += 0.2
                match_factors.append('model')
            
            # Title similarity
            title_similarity = fuzz.ratio(target_title, str(row['title']).lower()) / 100
            if title_similarity > 0.7:
                similarity_score += title_similarity * 0.3
                match_factors.append('title')
            
            if similarity_score >= threshold:
                similar_watches.append({
                    'index': idx,
                    'similarity_score': similarity_score,
                    'match_factors': match_factors,
                    'watch_data': row.to_dict()
                })
        
        # Sort by similarity score
        similar_watches.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return similar_watches
    
    def compare_prices(self, watch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare prices for similar watches"""
        similar_watches = self.find_similar_watches(watch_data)
        
        if not similar_watches:
            return {'message': 'No similar watches found'}
        
        prices = []
        for watch in similar_watches:
            price = watch['watch_data'].get('price')
            if price and price > 0:
                prices.append({
                    'price': price,
                    'site': watch['watch_data'].get('site'),
                    'url': watch['watch_data'].get('url'),
                    'title': watch['watch_data'].get('title')
                })
        
        if not prices:
            return {'message': 'No price data available for similar watches'}
        
        price_values = [p['price'] for p in prices]
        
        return {
            'similar_watches_count': len(similar_watches),
            'price_data_available': len(prices),
            'average_price': np.mean(price_values),
            'median_price': np.median(price_values),
            'min_price': min(price_values),
            'max_price': max(price_values),
            'price_range': max(price_values) - min(price_values),
            'price_details': prices,
            'recommended_price': min(price_values) - 100  # £100 below cheapest
        }
    
    def export_analysis(self, output_file: str):
        """Export comprehensive analysis to file"""
        analysis = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'statistics': self.generate_statistics(),
            'data_quality': self.assess_data_quality()
        }
        
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print(f"Analysis exported to {output_file}")
    
    def assess_data_quality(self) -> Dict[str, Any]:
        """Assess the quality of scraped data"""
        if self.df is None:
            return {}
        
        total_records = len(self.df)
        
        quality_metrics = {
            'completeness': {
                'title': (self.df['title'].notna().sum() / total_records) * 100,
                'price': (self.df['price'].notna().sum() / total_records) * 100,
                'brand': (self.df['brand'].notna().sum() / total_records) * 100,
                'reference': (self.df['reference'].notna().sum() / total_records) * 100,
                'images': (self.df['images'].notna().sum() / total_records) * 100
            },
            'data_distribution': {
                'sites_with_data': self.df['site'].value_counts().to_dict(),
                'brands_with_data': self.df['brand'].value_counts().to_dict()
            }
        }
        
        return quality_metrics

class WatchMatcher:
    """Match watches with external sources (Chrono24, Google Shopping)"""
    
    def __init__(self):
        self.match_threshold = 0.8
    
    def calculate_similarity(self, watch1: Dict, watch2: Dict) -> float:
        """Calculate similarity between two watches"""
        score = 0.0
        
        # Brand similarity (40% weight)
        if watch1.get('brand') and watch2.get('brand'):
            brand_sim = fuzz.ratio(
                str(watch1['brand']).lower(),
                str(watch2['brand']).lower()
            ) / 100
            score += brand_sim * 0.4
        
        # Reference similarity (30% weight)
        if watch1.get('reference') and watch2.get('reference'):
            ref_sim = fuzz.ratio(
                str(watch1['reference']).lower(),
                str(watch2['reference']).lower()
            ) / 100
            score += ref_sim * 0.3
        
        # Model similarity (20% weight)
        if watch1.get('model') and watch2.get('model'):
            model_sim = fuzz.ratio(
                str(watch1['model']).lower(),
                str(watch2['model']).lower()
            ) / 100
            score += model_sim * 0.2
        
        # Title similarity (10% weight)
        if watch1.get('title') and watch2.get('title'):
            title_sim = fuzz.ratio(
                str(watch1['title']).lower(),
                str(watch2['title']).lower()
            ) / 100
            score += title_sim * 0.1
        
        return score
    
    def match_watches(self, source_watches: List[Dict], target_watches: List[Dict]) -> Dict[str, Any]:
        """Match watches between two datasets"""
        matches = []
        unmatched_source = []
        unmatched_target = list(target_watches)
        
        for source_watch in source_watches:
            best_match = None
            best_score = 0
            
            for i, target_watch in enumerate(unmatched_target):
                similarity = self.calculate_similarity(source_watch, target_watch)
                
                if similarity > best_score and similarity >= self.match_threshold:
                    best_score = similarity
                    best_match = (i, target_watch, similarity)
            
            if best_match:
                idx, matched_watch, score = best_match
                matches.append({
                    'source_watch': source_watch,
                    'matched_watch': matched_watch,
                    'similarity_score': score
                })
                unmatched_target.pop(idx)
            else:
                unmatched_source.append(source_watch)
        
        return {
            'matches': matches,
            'unmatched_source': unmatched_source,
            'unmatched_target': unmatched_target,
            'match_rate': len(matches) / len(source_watches) if source_watches else 0
        }

if __name__ == "__main__":
    # Example usage
    processor = WatchDataProcessor()
    
    # If you have a data file
    # processor.load_data('data/consolidated_watches.csv')
    # processor.clean_data()
    # stats = processor.generate_statistics()
    # print(json.dumps(stats, indent=2))
    
    print("Data processing utilities ready!")
