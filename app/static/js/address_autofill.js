/**
 * 郵便番号から住所を自動入力する機能を初期化します。
 * この関数は、代表者用と税理士用など、複数の住所入力欄セットに再利用できます。
 *
 * @param {string} zipCodeFieldId - 郵便番号の入力欄のID
 * @param {string} prefectureFieldId - 都道府県の入力欄のID
 * @param {string} cityFieldId - 市区町村の入力欄のID
 * @param {string} addressFieldId - 住所（番地以降）の入力欄のID
 */
function initializeAddressAutofill(zipCodeFieldId, prefectureFieldId, cityFieldId, addressFieldId) {
  const zipCodeField = document.getElementById(zipCodeFieldId);
  const prefectureField = document.getElementById(prefectureFieldId);
  const cityField = document.getElementById(cityFieldId);
  const addressField = document.getElementById(addressFieldId);

  // 必須の要素がページに存在するか確認します
  if (!zipCodeField || !prefectureField || !cityField || !addressField) {
    console.error("Address autofill failed: One or more specified element IDs were not found in the DOM.", {
      zipCodeFieldId, prefectureFieldId, cityFieldId, addressFieldId
    });
    return;
  }

  // 郵便番号入力欄でキー入力が終わったタイミングでイベントを発火させます
  zipCodeField.addEventListener('keyup', async () => {
    const zipCode = zipCodeField.value.replace(/-/g, '');
    if (zipCode.length !== 7) {
      return;
    }

    try {
      // ZipCloud APIへリクエストを送信します
      const response = await fetch(`https://zipcloud.ibsnet.co.jp/api/search?zipcode=${zipCode}`);
      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }
      
      const data = await response.json();

      if (data.status === 200 && data.results) {
        const result = data.results[0];
        prefectureField.value = result.address1;
        cityField.value = result.address2;
        addressField.value = result.address3 || '';
        
        // 番地以降の入力に集中できるよう、カーソルを移動します
        addressField.focus(); 
      } else {
        console.warn("Address not found for this zip code:", zipCode, "API Message:", data.message);
      }
    } catch (error) {
      console.error("An error occurred during the address fetch operation:", error);
    }
  });
}

// DOMの読み込みが完了したら、各住所欄の自動入力機能を有効化します
document.addEventListener('DOMContentLoaded', () => {
  // 代表者の住所欄を初期化
  initializeAddressAutofill(
    'representative_zip_code',
    'representative_prefecture',
    'representative_city',
    'representative_address'
  );

  // 税理士の住所欄を初期化
  initializeAddressAutofill(
    'tax_accountant_zip',
    'tax_accountant_prefecture',
    'tax_accountant_city',
    'tax_accountant_address'
  );
});
