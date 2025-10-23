const http = require('http');

const options = {
  hostname: 'localhost',
  port: 8001,
  path: '/demo',
  method: 'GET'
};

const req = http.request(options, (res) => {
  let data = '';

  res.on('data', (chunk) => {
    data += chunk;
  });

  res.on('end', () => {
    console.log('🔍 프론트엔드 페이지 분석');
    console.log('='.repeat(60));

    // 1. 주요 요소 확인
    console.log('\n1️⃣ 주요 HTML 요소:');
    console.log(`  - <input id="chatInput">: ${data.includes('id="chatInput"') ? '✅' : '❌'}`);
    console.log(`  - <button id="sendButton">: ${data.includes('id="sendButton"') ? '✅' : '❌'}`);
    console.log(`  - .product-list: ${data.includes('class="product-list"') ? '✅' : '❌'}`);
    console.log(`  - #detailModal: ${data.includes('id="detailModal"') ? '✅' : '❌'}`);

    // 2. CSS 확인
    console.log('\n2️⃣ CSS 스타일:');
    console.log(`  - .product-image: ${data.includes('.product-image') ? '✅' : '❌'}`);
    console.log(`  - overflow-y: auto: ${data.includes('overflow-y: auto') ? '✅' : '❌'}`);
    console.log(`  - modal.active: ${data.includes('.modal.active') ? '✅' : '❌'}`);

    // 3. JavaScript 함수
    console.log('\n3️⃣ JavaScript 함수:');
    console.log(`  - sendMessage(): ${data.includes('function sendMessage') ? '✅' : '❌'}`);
    console.log(`  - showDetail(): ${data.includes('function showDetail') ? '✅' : '❌'}`);
    console.log(`  - init(): ${data.includes('function init()') ? '✅' : '❌'}`);

    // 4. WebSocket 초기화
    console.log('\n4️⃣ WebSocket 설정:');
    console.log(`  - ws = new WebSocket: ${data.includes('ws = new WebSocket') ? '✅' : '❌'}`);
    console.log(`  - ws.onopen: ${data.includes('ws.onopen') ? '✅' : '❌'}`);
    console.log(`  - ws.onmessage: ${data.includes('ws.onmessage') ? '✅' : '❌'}`);

    // 5. 이미지 렌더링
    console.log('\n5️⃣ 이미지 렌더링 코드:');
    console.log(`  - class="product-image": ${data.includes('class="product-image"') ? '✅' : '❌'}`);
    console.log(`  - onerror 핸들러: ${data.includes('onerror=') ? '✅' : '❌'}`);

    // 6. 모달 구조
    console.log('\n6️⃣ 모달 구조:');
    console.log(`  - #detailModal: ${data.includes('id="detailModal"') ? '✅' : '❌'}`);
    console.log(`  - #compareModal: ${data.includes('id="compareModal"') ? '✅' : '❌'}`);

    // 7. 파일 크기
    console.log('\n7️⃣ 파일 정보:');
    console.log(`  - HTML 파일 크기: ${data.length} bytes`);

    console.log('\n' + '='.repeat(60));
    console.log('✨ 페이지 구조 검증 완료');
  });
});

req.on('error', (e) => {
  console.error(`❌ 요청 실패: ${e.message}`);
});

req.end();
