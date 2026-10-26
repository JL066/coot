// Test-only inspection of the existing HUD; never installed into Coot.app.
#include "graphics-info.h"

extern "C" void rama_probe(double *out) {
   graphics_info_t g;
   out[0] = g.backbone_torsion_rama_active;
   out[1] = g.gl_rama_plot.get_number_of_phi_psi();
   out[2] = out[1] ? g.gl_rama_plot.get_number_of_outliers() : -1;
   out[3] = g.draw_gl_ramachandran_plot_flag;
   int i = 8;
   for (const auto &entry : g.gl_rama_plot.phi_psi_map) {
      if (i >= 12) break;
      out[i++] = entry.second.phi;
      out[i++] = entry.second.psi;
   }
   if (g.backbone_torsion_rama_active && g.moving_atoms_asc) {
      const auto p = g.phi_psi_pairs_from_moving_atoms();
      out[4] = p.first.first; out[5] = p.first.second;
      out[6] = p.second.first; out[7] = p.second.second;
   }
}

// Capture the renderer's test framebuffer after GtkGLArea's render callback.
extern "C" int rama_capture(const char *path) {
   GLint viewport[4];
   glGetIntegerv(GL_VIEWPORT, viewport);
   const int w = viewport[2], h = viewport[3];
   if (w <= 0 || h <= 0) return 0;
   std::vector<unsigned char> pixels(w * h * 4);
   glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());
   GdkPixbuf *raw = gdk_pixbuf_new_from_data(pixels.data(), GDK_COLORSPACE_RGB,
                                           TRUE, 8, w, h, w * 4, nullptr, nullptr);
   GdkPixbuf *flipped = gdk_pixbuf_flip(raw, FALSE);
   const bool ok = gdk_pixbuf_save(flipped, path, "png", nullptr, nullptr);
   g_object_unref(flipped);
   g_object_unref(raw);
   return ok;
}
