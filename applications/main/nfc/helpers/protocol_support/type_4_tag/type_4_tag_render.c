#include "type_4_tag_render.h"

#include "../iso14443_4a/iso14443_4a_render.h"

void nfc_render_type_4_tag_info(
    const Type4TagData* data,
    NfcProtocolFormatType format_type,
    FuriString* str) {
    nfc_render_iso14443_4a_brief(type_4_tag_get_base_data(data), str);

    furi_string_cat(str, "\n:::::::::::::::[Ulozena data NDEF]:::::::::::::::\n");
    furi_string_cat_printf(str, "Aktualni velikost NDEF: %lu", simple_array_get_count(data->ndef_data));

    if(data->is_tag_specific) {
        furi_string_cat(str, "\n::::::::::::::::::[Parametry tagu]::::::::::::::::::\n");
        furi_string_cat_printf(
            str,
            "Karta: %s\n",
            furi_string_empty(data->platform_name) ? "nezname" :
                                                     furi_string_get_cstr(data->platform_name));
        furi_string_cat_printf(
            str, "Verze mapovani T4T: %u.%u\n", data->t4t_version.major, data->t4t_version.minor);
        furi_string_cat_printf(str, "ID souboru NDEF: %04X\n", data->ndef_file_id);
        furi_string_cat_printf(str, "Max. velikost NDEF: %u\n", data->ndef_max_len);
        furi_string_cat_printf(
            str, "Velikost APDU: cteni %u, zapis %u\n", data->chunk_max_read, data->chunk_max_write);
        furi_string_cat_printf(
            str,
            "Zamek cteni: %02X%s\n",
            data->ndef_read_lock,
            data->ndef_read_lock == 0 ? " (odemceno)" : "");
        furi_string_cat_printf(
            str,
            "Zamek zapisu: %02X%s",
            data->ndef_write_lock,
            data->ndef_write_lock == 0 ? " (odemceno)" : "");
    }

    if(format_type != NfcProtocolFormatTypeFull) return;

    furi_string_cat(str, "\n\e#Udaje ISO14443-4");
    nfc_render_iso14443_4a_extra(type_4_tag_get_base_data(data), str);
}

void nfc_render_type_4_tag_dump(const Type4TagData* data, FuriString* str) {
    size_t ndef_len = simple_array_get_count(data->ndef_data);
    if(ndef_len == 0) {
        furi_string_cat_str(str, "Zadna data NDEF k zobrazeni");
        return;
    }
    const uint8_t* ndef_data = simple_array_cget_data(data->ndef_data);
    furi_string_cat_printf(str, "\e*");
    for(size_t i = 0; i < ndef_len; i += TYPE_4_TAG_RENDER_BYTES_PER_LINE) {
        const uint8_t* line_data = &ndef_data[i];
        for(size_t j = 0; j < TYPE_4_TAG_RENDER_BYTES_PER_LINE; j += 2) {
            furi_string_cat_printf(str, " %02X%02X", line_data[j], line_data[j + 1]);
        }
    }
}
