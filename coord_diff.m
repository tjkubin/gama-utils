#!/usr/bin/octave -q

% computes covariance matrix of coordinate differences of two points
% cm_file  ...  covariance matrix
% p1, p12  ...  indexes of point 1 and point 2
% dim      ...  network points dimension (1,2,3)


argv = argv();
if length(argv) != 4
  error('usage: coord_diff.m cov_mat_file dim point_1_ind point_2_ind')
end

cm_file = argv{1};
dim = str2num(argv{2});
p1 = str2num(argv{3});
p2 = str2num(argv{4});

p1ind = (p1 - 1)*dim + 1;
p2ind = (p2 - 1)*dim + 1;

printf('Points: %i(%i) - %i(%i)\n', p1, p1ind, p2, p2ind)

cm = load(cm_file);
%size(cm)

c1 = cm(p1ind:p1ind+2,p1ind:p1ind+2);
c2 = cm(p2ind:p2ind+2,p2ind:p2ind+2);
c12 = cm(p1ind:p1ind+2,p2ind:p2ind+2);

printf('Covariance matrix:\n')
cd = c1 - 2*c12 + c2

cx = cd(1,1); cy = cd(2,2); cz = cd(3,3);
mxy = sqrt((cx + cy)/2);
printf('m_xy: %.3f\n', mxy)
mz = sqrt(cz);
printf('m_z: %.3f\n\n', mz)

%det(c1)
%det(c2)
%det(c12)
%det(cd)
