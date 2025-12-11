# Models Directory

هذا المجلد يحتوي على جميع النماذج المدربة للتطبيق بشكل منظم.

## البنية (Structure)

```
models/
├── gender/          # نماذج التنبؤ بالجنس
├── region/          # نماذج التنبؤ بالمنطقة/الأصل
├── predictors.py    # كود تحميل واستخدام النماذج
└── __init__.py      # Package initialization
```

## Gender Models (نماذج الجنس)

**المسار:** `models/gender/`

**الملفات المطلوبة:**
- `best_sex_model.pkl` أو `best_gender_model.pkl` - النموذج الرئيسي ✅
- `ensemble_sex_model.pkl` أو `ensemble_gender_model.pkl` - النموذج المجمع (اختياري)
- `feature_selector.pkl` - محدد الخصائص
- `pca_model.pkl` - نموذج PCA
- `sex_features_pca.csv` - بيانات الخصائص
- `sex_selected_snps.csv` - SNPs المختارة

**ملاحظة:** النماذج تدعم تسميتين مختلفتين (sex/gender) للتوافق الخلفي.

## Region/Ancestry Models (نماذج المنطقة/الأصل)

**المسار:** `models/region/`

**الملفات المطلوبة:**
- `best_population_model.pkl` - النموذج الرئيسي ✅
- `population_encoder.pkl` - المشفر ✅
- `genetic_features_pca.csv` - بيانات الخصائص
- `pca_model.pkl` - نموذج PCA (اختياري)
- `selected_snps.csv` - SNPs المختارة (اختياري)

## كيفية التحقق من النماذج

قم بتشغيل السكريبت التالي للتحقق من أن جميع النماذج موجودة وتعمل:

```bash
python verify_models.py
```

## عند نشر المشروع (Deployment)

**مهم جداً:** تأكد من نسخ مجلد `models/` بالكامل عند نقل المشروع لجهاز آخر!

الملفات التي يجب نسخها:
1. ✅ جميع ملفات `.pkl` - النماذج المدربة
2. ✅ جميع ملفات `.csv` - البيانات المساعدة
3. ✅ ملفات `.py` - الكود البرمجي

**ملاحظة:** ملفات النماذج كبيرة الحجم (عدة MB) لذلك تأكد من:
- رفعها على Git LFS إذا كنت تستخدم Git
- أو نسخها يدوياً عند النشر
- أو استخدام storage منفصل للنماذج

## استكشاف الأخطاء (Troubleshooting)

### خطأ: "gender model not found"

**الحل:**
1. تأكد من وجود مجلد `models/gender/`
2. تحقق من وجود ملف `best_sex_model.pkl` أو `best_gender_model.pkl`
3. قم بتشغيل `python verify_models.py` للتشخيص

### خطأ: "region model not found"

**الحل:**
1. تأكد من وجود مجلد `models/region/`
2. تحقق من وجود `best_population_model.pkl` و `population_encoder.pkl`
3. قم بتشغيل `python verify_models.py` للتشخيص

## التحديثات الأخيرة

- **8 ديسمبر 2025:** تم إعادة تنظيم النماذج من مجلدات متعددة (`hapmap_data/`, `new_model/`) إلى بنية موحدة ومنظمة في `models/`
- تم تبسيط دالة `find_model_directories()` لتبحث فقط في مكان واحد
- تم إزالة المسارات المطلقة (Absolute Paths) واستبدالها بمسارات نسبية

