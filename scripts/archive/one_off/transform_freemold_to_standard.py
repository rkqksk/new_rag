#!/usr/bin/env python3
"""
Freemold 데이터를 Onehago 표준 구조로 변환

입력: Freemold 원시 크롤링 데이터 (pIdx, mIdx, specifications as string)
출력: Onehago 표준 구조 (product_id, company_no, specifications as dict)
"""
import json
from pathlib import Path
from datetime import datetime
import re


class FreemoldDataTransformer:
    def __init__(self):
        self.output_dir = Path('data/freemold/transformed')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 테이블 라벨 → 표준 필드명 매핑
        self.label_mapping = {
            '제품명': 'product_name',
            '제품코드': '코드',
            '코드': '코드',
            '제품규격': '사이즈',
            '규격': '사이즈',
            '사이즈': '사이즈',
            'Neck': 'Neck',
            '넥': 'Neck',
            'MOQ': 'MOQ',
            '최소주문수량': 'MOQ',
            '재질': '재질',
            '소재': '재질',
            '원산지': '원산지',
            '제조사': '제조사',
            '회사명': '제조사',
            'PHONE': 'PHONE',
            '전화': 'PHONE',
            '전화번호': 'PHONE',
            'FAX': 'FAX',
            '팩스': 'FAX',
            'E MAIL': 'E MAIL',
            'EMAIL': 'E MAIL',
            '이메일': 'E MAIL',
            '담당': '담당',
            '담당자': '담당'
        }

    def extract_specifications_dict(self, raw_product):
        """
        테이블 데이터를 specifications dict로 변환

        Freemold 원시 데이터는 플랫 구조:
        {
            'product_name': '...',
            'specifications': '제품규격 text',  # String
            'material': '재질 text',
            'moq': 'MOQ text',
            'origin': '원산지 text',
            'manufacturer': '제조사 text'
        }

        변환 후:
        {
            'specifications': {
                '코드': '...',
                '사이즈': '...',
                'Neck': '...',
                'MOQ': '...',
                '재질': '...',
                '원산지': '...',
                '제조사': '...',
                'PHONE': '...',
                'FAX': '...',
                'E MAIL': '...',
                '담당': '...'
            }
        }
        """
        specs_dict = {}

        # 기본 필드 매핑
        field_mappings = {
            'specifications': '사이즈',
            'material': '재질',
            'moq': 'MOQ',
            'origin': '원산지',
            'manufacturer': '제조사'
        }

        for raw_field, spec_field in field_mappings.items():
            value = raw_product.get(raw_field)
            if value and value not in ['None', 'N/A', '']:
                specs_dict[spec_field] = value

        # product_name에서 코드 추출 시도 (예: "제품명 (코드: ABC-123)")
        product_name = raw_product.get('product_name', '')
        code_match = re.search(r'코드[:\s]+([A-Z0-9-]+)', product_name, re.IGNORECASE)
        if code_match:
            specs_dict['코드'] = code_match.group(1)

        # URL에서 Neck 추출 시도 (예: URL에 neck=20 같은 파라미터)
        url = raw_product.get('url', '')
        neck_match = re.search(r'neck[=_](\d+)', url, re.IGNORECASE)
        if neck_match:
            specs_dict['Neck'] = f"Ø{neck_match.group(1)}"

        return specs_dict

    def transform_product(self, raw_product):
        """
        단일 제품을 Onehago 표준 구조로 변환
        """
        # specifications dict 생성
        specifications = self.extract_specifications_dict(raw_product)

        # 표준 구조로 변환
        transformed = {
            # ID 필드 (pIdx → product_id)
            'product_id': raw_product.get('pIdx', ''),
            'company_no': raw_product.get('mIdx', ''),
            'category_id': raw_product.get('category_code', ''),
            'category_name': raw_product.get('category_name', ''),

            # 기본 제품 정보
            'product_name': raw_product.get('product_name', ''),
            'detailed_name': raw_product.get('product_name', ''),  # Same as product_name
            'moq': raw_product.get('moq', ''),

            # URL 필드 (url → detail_url)
            'detail_url': raw_product.get('url', ''),

            # 이미지 필드
            'image_url': raw_product.get('main_image', ''),  # 메인 이미지
            'full_image_url': raw_product.get('main_image', ''),  # Same as image_url
            'image_path': '',  # TODO: 이미지 다운로드 후 설정
            'images': raw_product.get('images', []),  # 전체 이미지 리스트

            # specifications dict
            'specifications': specifications,

            # 개별 연락처 필드 (specifications에서 추출)
            'manufacturer': specifications.get('제조사', ''),
            'phone': specifications.get('PHONE', ''),
            'fax': specifications.get('FAX', ''),
            'email': specifications.get('E MAIL', ''),
            'contact': specifications.get('담당', ''),

            # 메타데이터
            'crawled_at': raw_product.get('crawled_at', datetime.now().isoformat())
        }

        return transformed

    def transform_batch(self, input_file, output_file=None):
        """
        배치 파일 변환
        """
        print(f"\n📂 입력 파일: {input_file}")

        # 원시 데이터 로드
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_products = json.load(f)

        print(f"✅ {len(raw_products)}개 제품 로드")

        # 변환
        transformed_products = []
        for raw in raw_products:
            transformed = self.transform_product(raw)
            transformed_products.append(transformed)

        # 출력 파일 설정
        if output_file is None:
            input_path = Path(input_file)
            output_file = self.output_dir / f"{input_path.stem}_transformed.json"

        # 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(transformed_products, f, ensure_ascii=False, indent=2)

        print(f"✅ 변환 완료: {output_file}")
        print(f"📊 총 {len(transformed_products)}개 제품 변환")

        # 샘플 출력
        if transformed_products:
            print("\n📄 변환 샘플 (첫 번째 제품):")
            sample = transformed_products[0]
            print(f"  product_id: {sample['product_id']}")
            print(f"  product_name: {sample['product_name']}")
            print(f"  moq: {sample['moq']}")
            print(f"  specifications: {json.dumps(sample['specifications'], ensure_ascii=False, indent=4)}")

        return output_file

    def validate_transformation(self, transformed_file, reference_file):
        """
        변환된 데이터가 참조 구조와 동일한 필드를 가지는지 검증
        """
        print(f"\n🔍 변환 검증")
        print(f"  변환 파일: {transformed_file}")
        print(f"  참조 파일: {reference_file}")

        # 파일 로드
        with open(transformed_file, 'r', encoding='utf-8') as f:
            transformed_data = json.load(f)

        with open(reference_file, 'r', encoding='utf-8') as f:
            reference_data = json.load(f)

        if not transformed_data or not reference_data:
            print("❌ 파일이 비어있습니다")
            return False

        # 필드 비교
        transformed_fields = set(transformed_data[0].keys())
        reference_fields = set(reference_data[0].keys())

        missing_fields = reference_fields - transformed_fields
        extra_fields = transformed_fields - reference_fields

        print(f"\n📊 필드 비교:")
        print(f"  참조 필드 수: {len(reference_fields)}")
        print(f"  변환 필드 수: {len(transformed_fields)}")

        if missing_fields:
            print(f"\n⚠️  누락된 필드: {missing_fields}")
        else:
            print(f"\n✅ 모든 필수 필드 존재")

        if extra_fields:
            print(f"\n💡 추가 필드: {extra_fields}")

        # 구조 샘플 비교
        print(f"\n📄 구조 비교 (첫 번째 제품):")
        print(f"\n--- 참조 (Onehago) ---")
        ref_sample = reference_data[0]
        for key in sorted(ref_sample.keys()):
            print(f"  {key}: {type(ref_sample[key]).__name__}")

        print(f"\n--- 변환 (Freemold) ---")
        trans_sample = transformed_data[0]
        for key in sorted(trans_sample.keys()):
            print(f"  {key}: {type(trans_sample[key]).__name__}")

        return len(missing_fields) == 0


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Freemold 데이터를 Onehago 표준 구조로 변환')
    parser.add_argument('input_file', help='입력 파일 (Freemold 원시 데이터)')
    parser.add_argument('--output', help='출력 파일 (선택적, 기본: data/freemold/transformed/)')
    parser.add_argument('--validate', help='참조 파일과 비교 검증',
                        default='/Users/oypnus/Project/rag-enterprise/data/onehago/test_clean/all_products_clean.json')

    args = parser.parse_args()

    print("=" * 70)
    print("🔄 FREEMOLD 데이터 변환 (→ Onehago 표준 구조)")
    print("=" * 70)

    transformer = FreemoldDataTransformer()

    # 변환
    output_file = transformer.transform_batch(args.input_file, args.output)

    # 검증 (참조 파일이 있으면)
    if args.validate and Path(args.validate).exists():
        transformer.validate_transformation(output_file, args.validate)

    print("\n" + "=" * 70)
    print("✅ 완료")
    print("=" * 70)


if __name__ == '__main__':
    main()
