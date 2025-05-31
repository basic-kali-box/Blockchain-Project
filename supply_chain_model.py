from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import json


class ProductCategory(Enum):
    """Enum representing different product categories"""
    FOOD = "food"
    CLOTHING = "clothing" 
    ELECTRONICS = "electronics"
    COSMETICS = "cosmetics"
    OTHER = "other"


class CertificationType(Enum):
    """Enum representing different certification types"""
    ORGANIC = "organic"
    FAIR_TRADE = "fair_trade"
    SUSTAINABLE = "sustainable"
    CARBON_NEUTRAL = "carbon_neutral"
    ECO_FRIENDLY = "eco_friendly"
    OTHER = "other"


class ActorType(Enum):
    """Enum representing different types of actors in the supply chain"""
    PRODUCER = "producer"
    PROCESSOR = "processor"
    DISTRIBUTOR = "distributor"
    RETAILER = "retailer"
    CERTIFIER = "certifier"
    CONSUMER = "consumer"


@dataclass
class Certification:
    """Represents a product certification"""
    certification_type: str  # One of CertificationType
    issuer: str
    issue_date: str
    expiry_date: str
    certification_id: str
    additional_info: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Location:
    """Represents a geographic location"""
    latitude: float
    longitude: float
    address: str
    country: str
    region: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProductRegistration:
    """Represents the initial registration of a product in the supply chain"""
    product_id: str
    name: str
    description: str
    category: str  # One of ProductCategory
    producer_id: str
    production_date: str
    origin_location: Location
    certifications: List[Certification]
    batch_number: str
    additional_info: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'product_id': self.product_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'producer_id': self.producer_id,
            'production_date': self.production_date,
            'origin_location': self.origin_location.to_dict(),
            'certifications': [cert.to_dict() for cert in self.certifications],
            'batch_number': self.batch_number,
            'additional_info': self.additional_info
        }


@dataclass
class ProcessingStep:
    """Represents a processing or transformation step in the supply chain"""
    process_id: str
    product_id: str
    actor_id: str
    actor_type: str  # One of ActorType
    process_type: str
    description: str
    timestamp: str
    location: Location
    inputs: List[str]  # List of input product/material IDs
    outputs: List[str]  # List of output product IDs
    certification_references: List[str]  # References to certifications
    additional_info: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'process_id': self.process_id,
            'product_id': self.product_id,
            'actor_id': self.actor_id,
            'actor_type': self.actor_type,
            'process_type': self.process_type,
            'description': self.description,
            'timestamp': self.timestamp,
            'location': self.location.to_dict(),
            'inputs': self.inputs,
            'outputs': self.outputs,
            'certification_references': self.certification_references,
            'additional_info': self.additional_info
        }


@dataclass
class TransferEvent:
    """Represents a transfer of a product between actors in the supply chain"""
    transfer_id: str
    product_id: str
    sender_id: str
    sender_type: str  # One of ActorType
    recipient_id: str
    recipient_type: str  # One of ActorType
    timestamp: str
    departure_location: Location
    arrival_location: Optional[Location]  # May be None if in transit
    estimated_arrival_time: Optional[str]
    transport_conditions: Dict[str, Any]  # e.g., temperature, humidity
    status: str  # e.g., "in transit", "delivered"
    additional_info: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        result = {
            'transfer_id': self.transfer_id,
            'product_id': self.product_id,
            'sender_id': self.sender_id,
            'sender_type': self.sender_type,
            'recipient_id': self.recipient_id,
            'recipient_type': self.recipient_type,
            'timestamp': self.timestamp,
            'departure_location': self.departure_location.to_dict(),
            'estimated_arrival_time': self.estimated_arrival_time,
            'transport_conditions': self.transport_conditions,
            'status': self.status,
            'additional_info': self.additional_info
        }
        
        if self.arrival_location:
            result['arrival_location'] = self.arrival_location.to_dict()
        
        return result


@dataclass
class Quality:
    """Represents a quality check or test result"""
    quality_id: str
    product_id: str
    inspector_id: str
    timestamp: str
    metrics: Dict[str, Any]  # Various quality metrics
    passed: bool
    notes: str
    additional_info: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RetailEvent:
    """Represents a retail event (product being sold to consumer)"""
    retail_id: str
    product_id: str
    retailer_id: str
    timestamp: str
    location: Location
    price: float
    currency: str
    additional_info: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'retail_id': self.retail_id,
            'product_id': self.product_id,
            'retailer_id': self.retailer_id,
            'timestamp': self.timestamp,
            'location': self.location.to_dict(),
            'price': self.price,
            'currency': self.currency,
            'additional_info': self.additional_info
        }


def transaction_factory(transaction_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Factory function to create the appropriate transaction type
    
    :param transaction_type: Type of transaction
    :param data: Transaction data
    :return: Formatted transaction data
    """
    # Add validation logic specific to each transaction type
    if transaction_type == "product_registration":
        # Validate required fields for product registration
        required = ['product_id', 'name', 'producer_id']
        if not all(k in data for k in required):
            raise ValueError(f"Missing required fields for product registration: {required}")
        
        # Process nested objects like Location and Certifications
        if 'origin_location' in data and isinstance(data['origin_location'], dict):
            data['origin_location'] = Location(**data['origin_location'])
        
        if 'certifications' in data and isinstance(data['certifications'], list):
            # Check if each certification is already a Certification object or needs to be converted
            new_certifications = []
            for cert in data['certifications']:
                if isinstance(cert, Certification):
                    new_certifications.append(cert)
                elif isinstance(cert, dict):
                    new_certifications.append(Certification(**cert))
                else:
                    raise ValueError(f"Certification data must be a dict or Certification object, not {type(cert)}" )
            data['certifications'] = new_certifications
        
        return ProductRegistration(**data).to_dict()
    
    elif transaction_type == "processing":
        # Validate required fields
        required = ['process_id', 'product_id', 'actor_id', 'process_type']
        if not all(k in data for k in required):
            raise ValueError(f"Missing required fields for processing step: {required}")
        
        # Process location
        if 'location' in data and isinstance(data['location'], dict):
            data['location'] = Location(**data['location'])
        
        return ProcessingStep(**data).to_dict()
    
    elif transaction_type == "transfer":
        # Validate required fields
        required = ['transfer_id', 'product_id', 'sender_id', 'recipient_id']
        if not all(k in data for k in required):
            raise ValueError(f"Missing required fields for transfer event: {required}")
        
        # Process locations
        if 'departure_location' in data and isinstance(data['departure_location'], dict):
            data['departure_location'] = Location(**data['departure_location'])
        
        if 'arrival_location' in data and isinstance(data['arrival_location'], dict):
            data['arrival_location'] = Location(**data['arrival_location'])
        
        return TransferEvent(**data).to_dict()
    
    elif transaction_type == "quality_check":
        return Quality(**data).to_dict()
    
    elif transaction_type == "retail":
        if 'location' in data and isinstance(data['location'], dict):
            data['location'] = Location(**data['location'])
        
        return RetailEvent(**data).to_dict()
    
    else:
        raise ValueError(f"Unknown transaction type: {transaction_type}")


def validate_transaction(transaction_type: str, data: Dict[str, Any]) -> bool:
    """
    Validate a transaction based on its type and data
    
    :param transaction_type: Type of transaction
    :param data: Transaction data
    :return: True if valid, False otherwise
    """
    try:
        transaction_factory(transaction_type, data)
        return True
    except (ValueError, TypeError, KeyError) as e:
        print(f"Validation error: {e}")
        return False
