#include "slix_render.h"

void nfc_render_slix_info(const SlixData* data, NfcProtocolFormatType format_type, FuriString* str) {
    nfc_render_iso15693_3_brief(slix_get_base_data(data), str);

    if(format_type != NfcProtocolFormatTypeFull) return;
    const SlixType slix_type = slix_get_type(data);

    furi_string_cat(str, "\n::::::::::::::::::[Hesla]:::::::::::::::::\n");

    static const char* slix_password_names[] = {
        "Cteni",
        "Zapis",
        "Soukromi",
        "Znicit",
        "EAS/AFI",
    };

    for(uint32_t i = 0; i < SlixPasswordTypeCount; ++i) {
        if(slix_type_supports_password(slix_type, i)) {
            furi_string_cat_printf(
                str, "%s :  %08lX\n", slix_password_names[i], data->passwords[i]);
        }
    }

    furi_string_cat(str, ":::::::::::::::::::[Bity zamceni]::::::::::::::::::::\n");

    if(slix_type_has_features(slix_type, SLIX_TYPE_FEATURE_EAS)) {
        furi_string_cat_printf(
            str, "EAS: %s zamceno\n", data->system_info.lock_bits.eas ? "" : "neni");
    }

    if(slix_type_has_features(slix_type, SLIX_TYPE_FEATURE_PROTECTION)) {
        furi_string_cat_printf(
            str, "PPL: %s zamceno\n", data->system_info.lock_bits.ppl ? "" : "neni");

        const SlixProtection protection = data->system_info.protection;

        furi_string_cat(str, "::::::::::::[Ochrana stranek]::::::::::::\n");
        furi_string_cat_printf(str, "Ukazatel: H >= %02X\n", protection.pointer);

        const char* rh = (protection.condition & SLIX_PP_CONDITION_RH) ? "chraneno" : "nechraneno";
        const char* rl = (protection.condition & SLIX_PP_CONDITION_RL) ? "chraneno" : "nechraneno";

        const char* wh = (protection.condition & SLIX_PP_CONDITION_WH) ? "chraneno" : "nechraneno";
        const char* wl = (protection.condition & SLIX_PP_CONDITION_WL) ? "chraneno" : "nechraneno";

        furi_string_cat_printf(str, "C: H %s, L %s\n", rh, rl);
        furi_string_cat_printf(str, "Z: H %s, L %s\n", wh, wl);
    }

    if(slix_type_has_features(slix_type, SLIX_TYPE_FEATURE_PRIVACY)) {
        furi_string_cat(str, "::::::::::::::::::::[Soukromi]::::::::::::::::::::::\n");
        furi_string_cat_printf(str, "Rezim soukromi: %s\n", data->privacy ? "zapnut" : "vypnut");
    }

    if(slix_type_has_features(slix_type, SLIX_TYPE_FEATURE_SIGNATURE)) {
        furi_string_cat(str, ":::::::::::::::::::[Podpis]::::::::::::::::::\n");
        for(uint32_t i = 0; i < 4; ++i) {
            furi_string_cat_printf(str, "%02X ", data->signature[i]);
        }

        furi_string_cat(str, "[ ... ]");

        for(uint32_t i = 0; i < 3; ++i) {
            furi_string_cat_printf(str, " %02X", data->signature[sizeof(SlixSignature) - i - 1]);
        }
    }

    furi_string_cat(str, "\n\e#Udaje ISO15693-3");
    nfc_render_iso15693_3_extra(slix_get_base_data(data), str);
}
