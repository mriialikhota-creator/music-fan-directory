#include <iostream>
#include <cstring>
#include <vector>
#include <algorithm>
#include <cctype>

struct SongC {
    int id;
    double popularity;
    int duration;
    char title[100];
    char artist[100];
    char genre[50];
    char album[100];
};

struct AlbumC {
    int id;
    int year;
    char title[100];
};

bool str_contains_case_insensitive(const char* haystack, const char* needle) {
    if (!needle || !*needle) return true;
    std::string h_str = haystack;
    std::string n_str = needle;
    std::transform(h_str.begin(), h_str.end(), h_str.begin(), [](unsigned char c){ return std::tolower(c); });
    std::transform(n_str.begin(), n_str.end(), n_str.begin(), [](unsigned char c){ return std::tolower(c); });
    return h_str.find(n_str) != std::string::npos;
}

extern "C" {

    // лінійний пошук
    int filter_songs(SongC* songs, int count, const char* query, int* out_indices, int max_results, int search_mode) {
        int found_count = 0;
        for (int i = 0; i < count && found_count < max_results; i++) {
            bool match = false;

            if (search_mode == 0) { // All
                match = str_contains_case_insensitive(songs[i].title, query) ||
                        str_contains_case_insensitive(songs[i].artist, query) ||
                        str_contains_case_insensitive(songs[i].genre, query) ||
                        str_contains_case_insensitive(songs[i].album, query);
            } else if (search_mode == 1) { // Title
                match = str_contains_case_insensitive(songs[i].title, query);
            } else if (search_mode == 2) { // Artist
                match = str_contains_case_insensitive(songs[i].artist, query);
            } else if (search_mode == 3) { // Genre
                match = str_contains_case_insensitive(songs[i].genre, query);
            } else if (search_mode == 4) { // Album
                match = str_contains_case_insensitive(songs[i].album, query);
            }

            if (match) {
                out_indices[found_count++] = songs[i].id;
            }
        }
        return found_count;
    }

    int compare_songs(const SongC& a, const SongC& b, int mode, int asc) {
        bool result = false;
        if (mode == 0) result = a.popularity < b.popularity;
        else if (mode == 1) result = a.duration < b.duration;
        else if (mode == 2) result = strcmp(a.title, b.title) < 0;
        else if (mode == 3) result = strcmp(a.artist, b.artist) < 0;
        else if (mode == 4) result = strcmp(a.genre, b.genre) < 0;
        else if (mode == 5) result = strcmp(a.album, b.album) < 0;
        else if (mode == 6) result = a.id < b.id;

        return asc ? result : !result;
    }

    void quicksort_impl(SongC* arr, int low, int high, int mode, int asc) {
        if (low < high) {
            SongC pivot = arr[high];
            int i = (low - 1);
            for (int j = low; j <= high - 1; j++) {
                if (compare_songs(arr[j], pivot, mode, asc)) {
                    i++;
                    std::swap(arr[i], arr[j]);
                }
            }
            std::swap(arr[i + 1], arr[high]);
            int pi = i + 1;
            quicksort_impl(arr, low, pi - 1, mode, asc);
            quicksort_impl(arr, pi + 1, high, mode, asc);
        }
    }

    void sort_songs(SongC* songs, int count, int mode, int ascending) {
        quicksort_impl(songs, 0, count - 1, mode, ascending);
    }

    // Інші функції (mergesort, binary) залишаємо без змін або копіюємо з попереднього разу
    void merge(AlbumC* arr, int left, int mid, int right) {
        int n1 = mid - left + 1;
        int n2 = right - mid;
        std::vector<AlbumC> L(n1), R(n2);
        for (int i = 0; i < n1; i++) L[i] = arr[left + i];
        for (int j = 0; j < n2; j++) R[j] = arr[mid + 1 + j];
        int i = 0, j = 0, k = left;
        while (i < n1 && j < n2) {
            if (L[i].year <= R[j].year) arr[k++] = L[i++];
            else arr[k++] = R[j++];
        }
        while (i < n1) arr[k++] = L[i++];
        while (j < n2) arr[k++] = R[j++];
    }
    void mergesort_impl(AlbumC* arr, int left, int right) {
        if (left < right) {
            int mid = left + (right - left) / 2;
            mergesort_impl(arr, left, mid);
            mergesort_impl(arr, mid + 1, right);
            merge(arr, left, mid, right);
        }
    }
    void sort_albums_by_year(AlbumC* albums, int count) {
        mergesort_impl(albums, 0, count - 1);
    }
    int binary_search_album(AlbumC* albums, int count, const char* query) {
        int left = 0, right = count - 1;
        while (left <= right) {
            int mid = left + (right - left) / 2;
            int res = strcmp(albums[mid].title, query);
            if (res == 0) return albums[mid].id;
            if (res < 0) left = mid + 1;
            else right = mid - 1;
        }
        return -1;
    }
    void get_top_n_greedy(SongC* songs, int count, int n) {
        sort_songs(songs, count, 0, 0);
    }
}