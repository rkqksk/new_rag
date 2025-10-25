"""
사출성형 대표 불량 이미지 생성 스크립트

5가지 대표 불량:
1. Flash (버)
2. Short Shot (미성형)
3. Sink Marks (침몰 자국)
4. Warpage (휨)
5. Burn Marks (탄화 자국)
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_defect_image(defect_name, description, filename):
    """불량 이미지 생성 (텍스트 기반 다이어그램)"""

    # 이미지 크기
    width, height = 800, 600

    # 배경색 설정 (불량 종류별)
    colors = {
        'Flash': ('#FFE5E5', '#FF0000'),           # 밝은 빨강
        'Short Shot': ('#E5F3FF', '#0066CC'),     # 밝은 파랑
        'Sink Marks': ('#FFF3E5', '#FF8800'),     # 밝은 주황
        'Warpage': ('#F0E5FF', '#8800CC'),        # 밝은 보라
        'Burn Marks': ('#E5E5E5', '#000000')      # 회색
    }

    bg_color, text_color = colors.get(defect_name, ('#FFFFFF', '#000000'))

    # 이미지 생성
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # 텍스트 추가
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        font_desc = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        font_detail = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    except:
        font_title = ImageFont.load_default()
        font_desc = ImageFont.load_default()
        font_detail = ImageFont.load_default()

    # 제목
    title_bbox = draw.textbbox((0, 0), defect_name, font=font_title)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((width - title_width) / 2, 50), defect_name, fill=text_color, font=font_title)

    # 설명
    desc_lines = description.split('\n')
    y_offset = 150
    for line in desc_lines:
        if line.strip():
            draw.text((50, y_offset), line.strip(), fill=text_color, font=font_desc)
            y_offset += 40

    # 불량 시각화 (간단한 도형)
    draw_defect_diagram(draw, defect_name, text_color)

    # 이미지 저장
    img.save(filename)
    print(f"✅ Generated: {filename}")


def draw_defect_diagram(draw, defect_name, color):
    """불량 유형별 간단한 시각화"""

    if defect_name == 'Flash':
        # 버 (parting line에서 튀어나온 재료)
        draw.rectangle([300, 350, 500, 500], outline=color, width=5)
        # 버 표시
        draw.polygon([(500, 400), (550, 400), (550, 450)], fill=color)
        draw.text((560, 410), "← Flash", fill=color)

    elif defect_name == 'Short Shot':
        # 미성형 (불완전한 충전)
        draw.rectangle([300, 350, 500, 500], outline=color, width=5)
        draw.rectangle([300, 350, 450, 500], fill=color)
        draw.text((460, 410), "← Unfilled", fill=color)

    elif defect_name == 'Sink Marks':
        # 침몰 자국 (표면 함몰)
        draw.rectangle([300, 350, 500, 500], outline=color, width=5)
        draw.ellipse([350, 400, 450, 450], outline=color, width=3)
        draw.text((360, 470), "Sink mark", fill=color)

    elif defect_name == 'Warpage':
        # 휨 (변형)
        points = [(300, 450), (350, 430), (400, 420), (450, 430), (500, 450)]
        draw.line(points, fill=color, width=5)
        draw.line([(300, 500), (500, 500)], fill=color, width=2)
        draw.text((350, 510), "Warped vs Flat", fill=color)

    elif defect_name == 'Burn Marks':
        # 탄화 자국
        draw.rectangle([300, 350, 500, 500], outline=color, width=5)
        draw.ellipse([380, 380, 420, 420], fill=color)
        draw.text((430, 390), "← Burn", fill=color)


def main():
    """5가지 대표 불량 이미지 생성"""

    defects = [
        {
            'name': 'Flash',
            'description': 'Excess material at parting line\nCauses:\n- Low clamping force\n- High injection pressure\n- Mold wear',
            'filename': 'defect_1_flash.png'
        },
        {
            'name': 'Short Shot',
            'description': 'Incomplete cavity filling\nCauses:\n- Insufficient injection pressure\n- Low melt temperature\n- Gate too small',
            'filename': 'defect_2_short_shot.png'
        },
        {
            'name': 'Sink Marks',
            'description': 'Surface depressions on thick sections\nCauses:\n- Non-uniform wall thickness\n- Insufficient packing pressure\n- Short cooling time',
            'filename': 'defect_3_sink_marks.png'
        },
        {
            'name': 'Warpage',
            'description': 'Dimensional distortion after cooling\nCauses:\n- Non-uniform cooling\n- Mold temperature imbalance\n- High injection speed',
            'filename': 'defect_4_warpage.png'
        },
        {
            'name': 'Burn Marks',
            'description': 'Discoloration from gas combustion\nCauses:\n- Air trapping\n- Excessive injection speed\n- Insufficient venting',
            'filename': 'defect_5_burn_marks.png'
        }
    ]

    print("🏭 Generating Injection Molding Defect Images...")
    print("=" * 60)

    for defect in defects:
        create_defect_image(
            defect['name'],
            defect['description'],
            defect['filename']
        )

    print("=" * 60)
    print(f"✅ Generated {len(defects)} defect images")
    print(f"📁 Location: {os.getcwd()}")


if __name__ == "__main__":
    main()
